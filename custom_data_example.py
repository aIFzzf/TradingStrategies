#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用自定义数据的回测示例
展示如何使用Yahoo Finance数据运行双均线策略
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategies import DualMAStrategy
from backtest_engine import get_stock_data, run_backtest, compare_strategies


def run_backtest_on_custom_data(symbol='AAPL', start_date='2020-01-01', end_date='2023-12-31'):
    """
    在自定义数据上运行回测
    
    参数:
    - symbol: 股票代码
    - start_date: 开始日期
    - end_date: 结束日期
    
    返回:
    - stats: 回测结果统计
    """
    print(f"获取 {symbol} 的数据...")
    data = get_stock_data(symbol, start_date, end_date)
    
    print(f"运行双均线策略回测...")
    stats, bt = run_backtest(data, DualMAStrategy)
    
    print("\n回测结果:")
    print(stats[['Start', 'End', 'Duration', 'Return [%]', 'Max. Drawdown [%]', 
                 '# Trades', 'Win Rate [%]', 'Sharpe Ratio']])
    
    # 绘制回测结果
    bt.plot()
    
    return stats, bt


def compare_multiple_stocks(symbols=['AAPL', 'MSFT', 'GOOG'], 
                           start_date='2020-01-01', 
                           end_date='2023-12-31'):
    """
    比较多个股票的策略表现
    
    参数:
    - symbols: 股票代码列表
    - start_date: 开始日期
    - end_date: 结束日期
    
    返回:
    - 比较结果DataFrame
    """
    results = {}
    
    for symbol in symbols:
        print(f"\n处理 {symbol}...")
        try:
            data = get_stock_data(symbol, start_date, end_date)
            
            # 创建策略配置
            strategies_config = [
                {
                    'name': f'{symbol} 双均线(10,30)',
                    'strategy_class': DualMAStrategy,
                    'params': {'fast_ma': 10, 'slow_ma': 30}
                },
                {
                    'name': f'{symbol} 双均线(5,20)',
                    'strategy_class': DualMAStrategy,
                    'params': {'fast_ma': 5, 'slow_ma': 20}
                }
            ]
            
            # 比较策略
            comparison = compare_strategies(data, strategies_config)
            
            # 保存结果
            for idx, row in comparison.iterrows():
                results[idx] = row.to_dict()
            
            print(f"{symbol} 处理完成")
        except Exception as e:
            print(f"处理 {symbol} 时出错: {e}")
    
    # 创建比较表格
    if results:
        comparison_df = pd.DataFrame(results).T
        
        # 保存到CSV
        comparison_df.to_csv('stock_comparison_results.csv')
        print("\n比较结果已保存到 stock_comparison_results.csv")
        
        return comparison_df
    
    return pd.DataFrame()


def plot_comparison_results(comparison_df):
    """
    绘制比较结果
    
    参数:
    - comparison_df: 比较结果DataFrame
    """
    if comparison_df.empty:
        print("没有可用的比较结果")
        return
    
    # 绘制回报率比较
    plt.figure(figsize=(12, 6))
    comparison_df['Return [%]'].sort_values().plot(kind='bar')
    plt.title('策略回报率比较')
    plt.ylabel('回报率 (%)')
    plt.xlabel('策略')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('return_comparison.png')
    
    # 绘制夏普比率比较
    plt.figure(figsize=(12, 6))
    comparison_df['Sharpe Ratio'].sort_values().plot(kind='bar')
    plt.title('策略夏普比率比较')
    plt.ylabel('夏普比率')
    plt.xlabel('策略')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('sharpe_comparison.png')
    
    print("比较图表已保存")


if __name__ == "__main__":
    # 运行单个股票的回测
    stats, bt = run_backtest_on_custom_data('AAPL', '2020-01-01', '2023-12-31')
    
    # 比较多个股票
    comparison_df = compare_multiple_stocks(['AAPL', 'MSFT', 'GOOG', 'AMZN'], 
                                           '2020-01-01', '2023-12-31')
    
    # 绘制比较结果
    if not comparison_df.empty:
        plot_comparison_results(comparison_df)
