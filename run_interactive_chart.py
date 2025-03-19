#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交互式图表 - 可切换周线和月线
"""

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategies import LongTermMACDStrategy
from backtest_engine import get_stock_data, run_backtest, resample_data


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='交互式图表 - 可切换周线和月线')
    
    parser.add_argument('--symbol', type=str, default='AAPL',
                        help='股票代码，例如 AAPL')
    
    parser.add_argument('--start', type=str, default='2018-01-01',
                        help='开始日期，格式 YYYY-MM-DD')
    
    parser.add_argument('--end', type=str, default='2023-12-31',
                        help='结束日期，格式 YYYY-MM-DD')
    
    parser.add_argument('--fast_period', type=int, default=12,
                        help='MACD快线周期')
    
    parser.add_argument('--slow_period', type=int, default=26,
                        help='MACD慢线周期')
    
    parser.add_argument('--signal_period', type=int, default=9,
                        help='MACD信号线周期')
    
    parser.add_argument('--ema_period', type=int, default=20,
                        help='日线EMA周期')
    
    parser.add_argument('--price_range_pct', type=float, default=0.05,
                        help='筹码集中区域上下浮动百分比')
    
    parser.add_argument('--stop_loss', type=float, default=0.05,
                        help='止损百分比')
    
    parser.add_argument('--take_profit', type=float, default=0.1,
                        help='止盈百分比')
    
    parser.add_argument('--position_size', type=float, default=1.0,
                        help='仓位大小，范围0.0-1.0，默认1.0表示全仓')
    
    parser.add_argument('--downtrend_exit_size', type=float, default=0.5,
                        help='趋势反转时卖出的仓位比例，默认0.5表示卖出一半')
    
    return parser.parse_args()


def run_interactive_chart(args):
    """运行交互式图表"""
    # 获取股票数据（使用缓存功能）
    data = get_stock_data(args.symbol, args.start, args.end, use_cache=True, cache_dir='data_cache')
    
    # 将数据重采样为周线和月线周期
    weekly_data = resample_data(data, interval='W')
    monthly_data = resample_data(data, interval='M')
    
    # 确保参数名称与策略类中定义的参数名称一致
    params = {
        'fast_period': args.fast_period,
        'slow_period': args.slow_period,
        'signal_period': args.signal_period,
        'ema_period': args.ema_period,
        'price_range_pct': args.price_range_pct,
        'stop_loss_pct': args.stop_loss,
        'take_profit_pct': args.take_profit,
        'position_size': args.position_size,
        'downtrend_exit_size': args.downtrend_exit_size
    }
    
    print(f"运行交互式图表，参数: {params}")
    
    # 创建策略实例并设置参数
    strategy = LongTermMACDStrategy
    strategy.fast_period = args.fast_period
    strategy.slow_period = args.slow_period
    strategy.signal_period = args.signal_period
    strategy.ema_period = args.ema_period
    strategy.price_range_pct = args.price_range_pct
    strategy.stop_loss_pct = args.stop_loss
    strategy.take_profit_pct = args.take_profit
    strategy.position_size = args.position_size
    strategy.downtrend_exit_size = args.downtrend_exit_size
    
    # 运行周线和月线回测
    weekly_stats, weekly_bt = run_backtest(weekly_data, strategy)
    monthly_stats, monthly_bt = run_backtest(monthly_data, strategy)
    
    print("\n周线回测结果:")
    print(weekly_stats[['Start', 'End', 'Duration', 'Return [%]', 'Max. Drawdown [%]', 
                 '# Trades', 'Win Rate [%]', 'Sharpe Ratio']])
    
    print("\n月线回测结果:")
    print(monthly_stats[['Start', 'End', 'Duration', 'Return [%]', 'Max. Drawdown [%]', 
                 '# Trades', 'Win Rate [%]', 'Sharpe Ratio']])
    
    # 询问用户选择查看哪种图表
    while True:
        choice = input("\n请选择要查看的图表类型 (1: 月线, 2: 周线, q: 退出): ")
        if choice == '1':
            print("显示月线图...")
            monthly_bt.plot()
        elif choice == '2':
            print("显示周线图...")
            weekly_bt.plot()
        elif choice.lower() == 'q':
            break
        else:
            print("无效的选择，请重新输入")
    
    return weekly_stats, monthly_stats, weekly_bt, monthly_bt


def main():
    """主函数"""
    args = parse_args()
    run_interactive_chart(args)


if __name__ == "__main__":
    main()
