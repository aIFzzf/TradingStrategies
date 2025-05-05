#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测引擎
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from backtesting import Backtest
from common.timeframe_utils import resample_to_timeframe
from strategies import DualMAStrategy, MACrossRSI
import os


def get_stock_data(symbol, start_date, end_date, interval='1d', max_retries=3, retry_delay=2, use_cache=True, cache_dir='data_cache'):
    """
    获取股票数据
    
    参数:
    - symbol: 股票代码
    - start_date: 开始日期
    - end_date: 结束日期
    - interval: 数据周期，可选值：'1d'(日线), '1wk'(周线), '1mo'(月线)
    - max_retries: 最大重试次数
    - retry_delay: 重试延迟（秒）
    - use_cache: 是否使用缓存
    - cache_dir: 缓存目录
    
    返回:
    - DataFrame: 股票数据
    """
    # 创建缓存目录（如果不存在）
    if use_cache and not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # 构建缓存文件路径
    cache_file = os.path.join(cache_dir, f"{symbol}_{start_date}_{end_date}_{interval}.csv")
    
    # 如果使用缓存且缓存文件存在，则从缓存加载数据
    if use_cache and os.path.exists(cache_file):
        try:
            print(f"从缓存加载 {symbol} 的数据...")
            data = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            if not data.empty:
                print(f"成功从缓存加载数据，共 {len(data)} 条记录")
                return data
            print("缓存数据为空，将重新获取数据")
        except Exception as e:
            print(f"读取缓存文件出错: {e}，将重新获取数据")
    
    # 如果没有使用缓存或缓存加载失败，则从网络获取数据
    for attempt in range(max_retries):
        try:
            print(f"从Yahoo Finance获取 {symbol} 的数据...")
            data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
            
            if data.empty:
                if attempt < max_retries - 1:
                    print(f"获取数据失败，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise ValueError(f"无法获取股票数据: {symbol}")
            
            # 处理可能的多级索引列
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            # 如果使用缓存，则保存数据到缓存文件
            if use_cache:
                try:
                    data.to_csv(cache_file)
                    print(f"数据已保存到缓存文件: {cache_file}")
                except Exception as e:
                    print(f"保存缓存文件出错: {e}")
            
            return data
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"获取数据时出错: {e}，{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            else:
                print(f"获取数据失败，已达到最大重试次数: {e}")
                raise


def resample_data(data, interval='W'):
    """
    重采样数据到指定周期
    
    参数:
    - data: DataFrame, 原始数据
    - interval: str, 目标周期，可选值：'W'(周), 'M'(月), 'Q'(季), 'Y'(年)
    
    返回:
    - DataFrame: 重采样后的数据
    """
    return resample_to_timeframe(data, interval)


def run_backtest(data, strategy_class, **strategy_params):
    """
    运行回测
    
    参数:
    - data: DataFrame, 股票数据
    - strategy_class: Strategy, 策略类
    - strategy_params: dict, 策略参数
    
    返回:
    - tuple: (stats, bt) 回测统计结果和回测对象
    """
    bt = Backtest(data, strategy_class, cash=10000, commission=.002, **strategy_params)
    stats = bt.run()
    return stats, bt


def optimize_strategy(data, strategy_class, params_dict, maximize='Return [%]', constraint=None):
    """
    优化策略参数
    
    参数:
    - data: DataFrame, 股票数据
    - strategy_class: Strategy, 策略类
    - params_dict: dict, 参数范围字典
    - maximize: str, 优化目标
    - constraint: function, 参数约束函数
    
    返回:
    - tuple: (stats, bt) 最优参数的回测统计结果和回测对象
    """
    bt = Backtest(data, strategy_class, cash=10000, commission=.002)
    stats = bt.optimize(
        **params_dict,
        maximize=maximize,
        constraint=constraint,
        method='grid',
        max_tries=100,
        return_heatmap=False
    )
    return stats, bt


def compare_strategies(data, strategies_dict):
    """
    比较不同策略的性能
    
    参数:
    - data: DataFrame, 股票数据
    - strategies_dict: dict, 策略字典 {策略名称: (策略类, 参数字典)}
    
    返回:
    - DataFrame: 比较结果
    """
    results = {}
    
    for name, (strategy_class, params) in strategies_dict.items():
        bt = Backtest(data, strategy_class, cash=10000, commission=.002, **params)
        stats = bt.run()
        results[name] = stats
    
    return pd.DataFrame(results)


def plot_equity_curves(strategies):
    """
    绘制多个策略的权益曲线
    
    参数:
    - strategies: dict, 策略字典 {策略名称: 回测对象}
    """
    plt.figure(figsize=(12, 6))
    
    for name, bt in strategies.items():
        equity = bt._equity_curve['Equity']
        equity.plot(label=name)
    
    plt.title('策略权益曲线对比')
    plt.xlabel('日期')
    plt.ylabel('权益')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    # 示例：获取苹果公司的数据
    data = get_stock_data('AAPL', '2020-01-01', '2023-12-31')
    
    # 示例：运行双均线策略回测
    stats, bt = run_backtest(data, DualMAStrategy)
    bt.plot()
    
    # 示例：比较不同策略
    strategies_dict = {
        '双均线(10,30)': (DualMAStrategy, {'fast_ma': 10, 'slow_ma': 30}),
        '双均线(5,20)': (DualMAStrategy, {'fast_ma': 5, 'slow_ma': 20}),
        'MA+RSI': (MACrossRSI, {})
    }
    
    comparison = compare_strategies(data, strategies_dict)
    print("\n策略比较结果:")
    print(comparison)
    
    # 绘制权益曲线比较
    strategies = {
        name: run_backtest(data, strategy_class, **params)[1] 
        for name, (strategy_class, params) in strategies_dict.items()
    }
    plot_equity_curves(strategies)
