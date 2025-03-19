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
                        help='包含股票代码的JSON文件路径')
    
    parser.add_argument('--start', type=str, default='2020-01-01',
                        help='开始日期，格式：YYYY-MM-DD')
    
    parser.add_argument('--end', type=str, default=None,
                        help='结束日期，格式：YYYY-MM-DD，默认为当前日期')
    
    parser.add_argument('--max_workers', type=int, default=5,
                        help='并行处理的最大工作线程数')
    
    parser.add_argument('--output', type=str, default='data/csv/strategy_results.csv',
                        help='输出结果文件名')
    
    parser.add_argument('--signal_only', action='store_true',
                        help='只输出有买入信号的股票')
    
    return parser.parse_args()


def analyze_stock(symbol, start_date, end_date, signal_only=False):
    """
    分析单个股票
    
    参数:
    - symbol: str, 股票代码
    - start_date: str, 开始日期
    - end_date: str, 结束日期
    - signal_only: bool, 是否只返回有买入信号的股票
    
    返回:
    - dict: 分析结果
    """
    try:
        print(f"分析股票: {symbol}")
        
        # 获取股票数据
        data = get_stock_data(symbol, start_date, end_date, use_cache=True, cache_dir='data_cache')
        
        if data.empty:
            print(f"警告: {symbol} 没有数据")
            return None
        
        # 运行策略
        strategy = LongTermMACDStrategy
        stats, bt = run_backtest(data, strategy)
        
        # 检查是否有买入信号
        has_buy_signal = False
        
        # 获取策略实例
        strategy_instance = bt._strategy
        
        # 检查是否处于上涨趋势
        if hasattr(strategy_instance, 'in_uptrend') and strategy_instance.in_uptrend:
            has_buy_signal = True
        
        # 如果只需要有买入信号的股票，且没有买入信号，则返回None
        if signal_only and not has_buy_signal:
            return None
        
        # 提取关键指标
        result = {
            'Symbol': symbol,
            'Return [%]': stats['Return [%]'],
            'Max. Drawdown [%]': stats['Max. Drawdown [%]'],
            '# Trades': stats['# Trades'],
            'Win Rate [%]': stats['Win Rate [%]'],
            'Sharpe Ratio': stats['Sharpe Ratio'],
            'Buy Signal': has_buy_signal,
            'Current Price': data['Close'].iloc[-1],
            'Last Date': data.index[-1].strftime('%Y-%m-%d')
        }
        
        return result
    except Exception as e:
        print(f"分析 {symbol} 时出错: {e}")
        return None


def batch_analyze_stocks(symbols, start_date, end_date, max_workers=5, signal_only=False):
    """
    批量分析股票
    
    参数:
    - symbols: list, 股票代码列表
    - start_date: str, 开始日期
    - end_date: str, 结束日期
    - max_workers: int, 并行处理的最大工作线程数
    - signal_only: bool, 是否只返回有买入信号的股票
    
    返回:
    - DataFrame: 分析结果
    """
    results = []
    
    # 使用线程池并行处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_symbol = {
            executor.submit(analyze_stock, symbol, start_date, end_date, signal_only): symbol 
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
        results_df = results_df.sort_values(by=['Buy Signal', 'Return [%]'], ascending=[False, False])
        
        return results_df
    else:
        print("没有找到符合条件的股票")
        return pd.DataFrame()


def main():
    """主函数"""
    args = parse_args()
    
    # 设置结束日期（如果未指定）
    if args.end is None:
        args.end = datetime.now().strftime('%Y-%m-%d')
    
    # 加载股票代码列表
    if os.path.exists(args.symbols_file):
        symbols = load_symbols_from_file(args.symbols_file)
    else:
        print(f"文件 {args.symbols_file} 不存在，尝试获取纳斯达克100成分股...")
        symbols = get_nasdaq100_symbols()
        
        if not symbols:
            print("获取股票代码失败，退出程序")
            return
    
    print(f"开始分析 {len(symbols)} 只股票，从 {args.start} 到 {args.end}")
    
    # 批量分析股票
    results_df = batch_analyze_stocks(
        symbols, 
        args.start, 
        args.end, 
        max_workers=args.max_workers,
        signal_only=args.signal_only
    )
    
    if not results_df.empty:
        # 确保目录存在
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        # 保存结果到CSV
        results_df.to_csv(args.output, index=False)
        print(f"分析结果已保存到 {args.output}")
        
        # 打印有买入信号的股票
        buy_signals = results_df[results_df['Buy Signal'] == True]
        if not buy_signals.empty:
            print("\n有买入信号的股票:")
            print(buy_signals[['Symbol', 'Return [%]', 'Win Rate [%]', 'Current Price', 'Last Date']])
        else:
            print("\n没有找到有买入信号的股票")
    else:
        print("分析结果为空")


if __name__ == "__main__":
    main()
