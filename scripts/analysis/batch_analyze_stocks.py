#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量分析股票，应用长期MACD策略
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

from strategies import LongTermMACDStrategy
from backtest_engine import get_stock_data, run_backtest
from scripts.analysis.get_nasdaq_top100 import get_nasdaq100_symbols, load_symbols_from_file


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='批量分析股票，应用长期MACD策略')
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
    
    return parser.parse_args()


def analyze_stock(symbol, start_date, end_date, signal_only=False, uptrend_only=False):
    """
    分析单个股票
    
    参数:
    - symbol: str, 股票代码
    - start_date: str, 开始日期
    - end_date: str, 结束日期
    - signal_only: bool, 是否只返回有买入信号的股票
    - uptrend_only: bool, 是否只返回处于上涨大趋势的股票
    
    返回:
    - dict: 分析结果
    """
    try:
        # 获取股票数据
        data = get_stock_data(symbol, start_date, end_date)
        if data is None or len(data) < 50:  # 确保有足够的数据
            return None
        
        # 预处理数据，删除NaN值
        data = data.dropna()
        if len(data) < 50:  # 再次确保有足够的数据
            return None
            
        # 运行回测获取性能统计数据和策略状态
        stats, bt = run_backtest(data, LongTermMACDStrategy)
        
        # 获取最后一个交易日的信号和趋势状态
        last_date = data.index[-1].strftime('%Y-%m-%d')
        
        # 检查是否有买入或卖出信号以及是否处于上涨大趋势
        buy_signal = False
        sell_signal = False
        in_uptrend = False
        
        # 通过查看策略的交易记录来确定最后一个交易日是否有信号
        if hasattr(bt, 'trades') and bt.trades:
            last_trade = bt.trades[-1]
            # 如果最后一笔交易是买入且在最后一个交易日附近
            if last_trade.size > 0 and abs((last_trade.entry_time - data.index[-1]).days) <= 5:
                buy_signal = True
            # 如果最后一笔交易是卖出且在最后一个交易日附近
            elif last_trade.size < 0 and abs((last_trade.exit_time - data.index[-1]).days) <= 5:
                sell_signal = True
        
        # 通过查看策略输出的日志来确定趋势状态
        strategy_logs = str(stats)
        if '上涨大趋势' in strategy_logs:
            in_uptrend = True
        
        # 如果只需要买入信号的股票，且没有买入信号，则返回None
        if signal_only and not buy_signal:
            return None
            
        # 如果只需要上涨大趋势的股票，且不在上涨大趋势中，则返回None
        if uptrend_only and not in_uptrend:
            return None
        
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


def batch_analyze_stocks(symbols, start_date, end_date, max_workers=5, signal_only=False, uptrend_only=False):
    """
    批量分析股票
    
    参数:
    - symbols: list, 股票代码列表
    - start_date: str, 开始日期
    - end_date: str, 结束日期
    - max_workers: int, 并行处理的最大工作线程数
    - signal_only: bool, 是否只返回有买入信号的股票
    - uptrend_only: bool, 是否只返回处于上涨大趋势的股票
    
    返回:
    - DataFrame: 分析结果
    """
    results = []
    
    # 使用线程池并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_symbol = {
            executor.submit(analyze_stock, symbol, start_date, end_date, signal_only, uptrend_only): symbol 
            for symbol in symbols
        }
        
        # 使用tqdm显示进度条
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
    
    # 加载股票代码
    if os.path.exists(args.symbols_file):
        symbols = load_symbols_from_file(args.symbols_file)
        print(f"已从 {args.symbols_file} 加载 {len(symbols)} 个股票代码")
    else:
        symbols = get_nasdaq100_symbols()
        print(f"已获取 {len(symbols)} 个纳斯达克100成分股")
    
    print(f"开始分析 {len(symbols)} 只股票，从 {args.start_date} 到 {args.end_date}")
    
    # 批量分析股票
    results_df = batch_analyze_stocks(
        symbols, 
        args.start_date, 
        args.end_date, 
        args.max_workers, 
        args.signal_only,
        args.uptrend_only
    )
    
    # 保存结果
    if results_df is not None and not results_df.empty:
        results_df.to_csv(args.output, index=False)
        print(f"分析结果已保存到 {args.output}")
        
        # 显示结果摘要
        print("\n分析结果摘要:")
        print(f"总共分析了 {len(symbols)} 只股票")
        print(f"符合条件的股票数量: {len(results_df)}")
        
        if args.signal_only:
            buy_signals = results_df[results_df['Buy Signal'] == 'Yes']
            print(f"有买入信号的股票数量: {len(buy_signals)}")
            
        if args.uptrend_only:
            uptrend_stocks = results_df[results_df['In Uptrend'] == 'Yes']
            print(f"处于上涨大趋势的股票数量: {len(uptrend_stocks)}")
    else:
        # 创建一个空的DataFrame并保存
        empty_df = pd.DataFrame(columns=['Date', 'Symbol', 'Name', 'Price', 'Buy Signal', 'Sell Signal', 'Return [%]', 'In Uptrend', 'Notes'])
        empty_df.to_csv(args.output, index=False)
        print(f"分析结果为空，已创建空文件 {args.output}")


if __name__ == "__main__":
    main()
