#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量分析股票，支持多种交易策略
"""

import os
import json
import pandas as pd
import argparse
import concurrent.futures
from datetime import datetime
from tqdm import tqdm
import sys

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入所有可用策略
from strategies.long_term_macd_strategy import LongTermMACDStrategy
from strategies.dual_ma_strategy import DualMAStrategy
from strategies.macd_strategy import MACDStrategy
from strategies.bollinger_strategy import BollingerBandStrategy
# from strategies.ma_rsi_strategy import MARSIStrategy
from backtest_engine import Backtest, get_stock_data, run_backtest
from scripts.analysis.get_nasdaq_top100 import load_symbols_from_file as load_nasdaq100
from scripts.analysis.get_hstech50 import load_symbols_from_file as load_hstech50


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='批量分析股票，应用交易策略')
    parser.add_argument('--symbols_file', type=str, default='data/json/nasdaq100_symbols.json',
                        help='股票代码文件路径')
    parser.add_argument('--start_date', type=str, default='2020-01-01',
                        help='开始日期，格式：YYYY-MM-DD')
    parser.add_argument('--end_date', type=str, default=datetime.now().strftime('%Y-%m-%d'),
                        help='结束日期，格式：YYYY-MM-DD')
    parser.add_argument('--max_workers', type=int, default=5,
                        help='并行处理的最大工作线程数')
    parser.add_argument('--signal_only', action='store_true',
                        help='只显示有买入信号的股票')
    parser.add_argument('--uptrend_only', action='store_true',
                        help='只显示处于上涨大趋势的股票')
    parser.add_argument('--output', type=str, default='nasdaq100_analysis.csv',
                        help='输出文件路径')
    parser.add_argument('--index', type=str, choices=['nasdaq100', 'hstech50'], default='nasdaq100',
                        help='要分析的指数，可选：nasdaq100, hstech50')
    parser.add_argument('--debug_symbol', type=str, default=None,
                        help='只分析指定的单个股票代码，用于调试')
    parser.add_argument('--strategy', type=str, default='long_term_macd',
                        choices=['long_term_macd', 'dual_ma', 'macd', 'bollinger', 'ma_rsi'],
                        help='要使用的策略')
    
    return parser.parse_args()


def analyze_stock(symbol, start_date, end_date, strategy_class=LongTermMACDStrategy, signal_only=False, uptrend_only=False):
    """
    分析单个股票
    
    参数:
    - symbol: str, 股票代码
    - start_date: str, 开始日期
    - end_date: str, 结束日期
    - strategy_class: Strategy类, 要使用的策略类，默认为LongTermMACDStrategy
    - signal_only: bool, 是否只返回有买入信号的股票
    - uptrend_only: bool, 是否只返回处于上涨大趋势的股票
    
    返回:
    - dict: 分析结果
    """
    try:
        print(f"开始分析股票 {symbol} hhhhhhhhhhh")
        # 获取股票数据
        data = get_stock_data(symbol, start_date, end_date)
        if data is None or len(data) < 50:  # 确保有足够的数据
            return None
        
        # 预处理数据，删除NaN值
        data = data.dropna()
        if len(data) < 50:  # 再次确保有足够的数据
            return None
            

        # 使用传入的策略类
        strategy = strategy_class

        # 运行回测获取性能统计数据和策略状态
        stats, bt = run_backtest(data, strategy)
        
        # 获取最后一个交易日的信号和趋势状态
        last_date = data.index[-1].strftime('%Y-%m-%d')
        
        # 检查是否有买入或卖出信号以及是否处于上涨大趋势
        buy_signal = False
        sell_signal = False
        in_uptrend = strategy.in_uptrend
        
        
        # 构建结果
        result = {
            'Date': last_date,
            'Symbol': symbol,
            'Name': data['Name'].iloc[0] if 'Name' in data.columns else symbol,
            'Price': data['Close'].iloc[-1],
            'Buy Signal': 'Yes' if buy_signal else 'No',
            'Sell Signal': 'Yes' if sell_signal else 'No',
            'Return [%]': stats['Return [%]'],
            'In Uptrend': 'Yes' if in_uptrend else 'No',
            'Notes': ''
        }
        
        return result
    except Exception as e:
        print(f"分析 {symbol} 时出错: {e}")
        return None


def batch_analyze_stocks(symbols, start_date, end_date, strategy_class=LongTermMACDStrategy, max_workers=5, signal_only=False, uptrend_only=False):
    """
    批量分析股票
    
    参数:
    - symbols: list, 股票代码列表
    - start_date: str, 开始日期
    - end_date: str, 结束日期
    - strategy_class: Strategy类, 要使用的策略类，默认为LongTermMACDStrategy
    - max_workers: int, 并行处理的最大工作线程数
    - signal_only: bool, 是否只返回有买入信号的股票
    - uptrend_only: bool, 是否只返回处于上涨大趋势的股票
    
    返回:
    - DataFrame: 分析结果
    """
    results = []
    
    # 使用线程池并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 创建任务
        future_to_symbol = {executor.submit(analyze_stock, symbol, start_date, end_date, strategy_class, signal_only, uptrend_only): symbol for symbol in symbols}
        
        # 收集结果
        for future in tqdm(concurrent.futures.as_completed(future_to_symbol), total=len(symbols), desc="分析进度"):
            symbol = future_to_symbol[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as e:
                print(f"{symbol} 生成结果时出错: {e}")
    
    # 转换为DataFrame
    if results:
        results_df = pd.DataFrame(results)
        
        # 按照买入信号和收益率排序
        if uptrend_only:
            results_df = results_df.sort_values(by=['In Uptrend', 'Return [%]'], ascending=[False, False])
        else:
            results_df = results_df.sort_values(by=['Buy Signal', 'Return [%]'], ascending=[False, False])
        
        return results_df
    else:
        print("没有找到符合条件的股票")
        return None


def main():
    """主函数"""
    args = parse_args()
    
    # 根据命令行参数选择策略
    strategy_map = {
        'long_term_macd': LongTermMACDStrategy,
        'dual_ma': DualMAStrategy,
        'macd': MACDStrategy,
        'bollinger': BollingerBandStrategy,
        # 'ma_rsi': MARSIStrategy
    }
    
    strategy_class = strategy_map.get(args.strategy, LongTermMACDStrategy)
    print(f"使用策略: {args.strategy}")
    
    
    # 加载股票代码
    if args.index == 'nasdaq100':
        if os.path.exists(args.symbols_file):
            symbols = load_nasdaq100(args.symbols_file)
            print(f"已从 {args.symbols_file} 加载 {len(symbols)} 个股票代码")
        else:
            # 如果没有找到文件，尝试从网络获取
            from scripts.analysis.get_nasdaq_top100 import get_nasdaq100_symbols
            symbols = get_nasdaq100_symbols()
            print(f"已获取 {len(symbols)} 个纳斯达克100成分股")
    elif args.index == 'hstech50':
        hstech_file = 'data/json/hstech50_symbols.json'
        if os.path.exists(hstech_file):
            symbols = load_hstech50(hstech_file)
            print(f"已从 {hstech_file} 加载 {len(symbols)} 个股票代码")
        else:
            # 如果没有找到文件，尝试从网络获取
            from scripts.analysis.get_hstech50 import get_hstech50_symbols
            symbols = get_hstech50_symbols()
            print(f"已获取 {len(symbols)} 个恒生科技指数成分股")
    
    # 处理debug模式：如果指定了debug_symbol，则只分析该股票
    if args.debug_symbol:
        debug_symbol = args.debug_symbol.upper()
        # 检查是否在已加载的股票列表中
        symbols_upper = [s.upper() for s in symbols]
        if debug_symbol in symbols_upper:
            # 找到原始大小写形式
            idx = symbols_upper.index(debug_symbol)
            original_symbol = symbols[idx]
            symbols = [original_symbol]
            print(f"*** 调试模式：只分析股票 {original_symbol} ***")
        else:
            print(f"警告：调试股票代码 {args.debug_symbol} 不在当前指数成分股列表中。")
            print(f"将直接使用该代码进行分析。")
            symbols = [args.debug_symbol]
    
    print(f"开始分析 {len(symbols)} 只股票，从 {args.start_date} 到 {args.end_date}")
    
    # 批量分析股票
    results_df = batch_analyze_stocks(
        symbols, 
        args.start_date, 
        args.end_date,
        strategy_class,
        args.max_workers, 
        args.signal_only, 
        args.uptrend_only
    )
    
    # 保存结果
    if results_df is not None and not results_df.empty:
        # 确保输出目录存在
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 保存到CSV
        results_df.to_csv(args.output, index=False)
        print(f"分析结果已保存到 {args.output}")
        
        # 显示结果摘要
        print("\n分析结果摘要:")
        print(f"总共分析了 {len(symbols)} 只股票")
        print(f"符合条件的股票: {len(results_df)}")
        
        # 显示买入信号的股票
        buy_signals = results_df[results_df['Buy Signal'] == 'Yes']
        if not buy_signals.empty:
            print(f"\n有买入信号的股票 ({len(buy_signals)}):")
            for _, row in buy_signals.iterrows():
                print(f"{row['Symbol']} - {row['Name']} - 价格: {row['Price']:.2f}")
        
        # 显示处于上涨大趋势的股票
        uptrends = results_df[results_df['In Uptrend'] == 'Yes']
        if not uptrends.empty:
            print(f"\n处于上涨大趋势的股票 ({len(uptrends)}):")
            for _, row in uptrends.iterrows():
                print(f"{row['Symbol']} - {row['Name']} - 价格: {row['Price']:.2f}")
    else:
        print("没有找到符合条件的股票，未生成分析结果文件")


if __name__ == "__main__":
    main()
