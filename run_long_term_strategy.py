#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行长期MACD交易策略示例
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import os
from strategies import LongTermMACDStrategy
from backtest_engine import get_stock_data, run_backtest, resample_data


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='运行长期MACD交易策略回测')
    
    parser.add_argument('--symbol', type=str, default='AAPL',
                        help='股票代码，例如 AAPL')
    
    parser.add_argument('--start', type=str, default='2017-01-01',
                        help='开始日期，格式 YYYY-MM-DD')
    
    parser.add_argument('--end', type=str, default='2024-12-31',
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
                        help='趋势反转时卖出的仓位比例，范围0.0-1.0，默认0.5表示卖出一半')
    
    parser.add_argument('--optimize', action='store_true',
                        help='是否优化策略参数')
    
    return parser.parse_args()


def run_long_term_macd_strategy(args):
    """运行长期MACD策略"""
    # 获取股票数据（使用缓存功能）
    data = get_stock_data(args.symbol, args.start, args.end, use_cache=True, cache_dir='data_cache')
    
    # 将数据重采样为月线周期
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
    
    print(f"运行长期MACD策略回测，参数: {params}")
    
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
    
    # 运行回测，使用月线数据
    stats, bt = run_backtest(monthly_data, strategy)
    
    print("\n回测结果:")
    print(stats[['Start', 'End', 'Duration', 'Return [%]', 'Max. Drawdown [%]', 
                 '# Trades', 'Win Rate [%]', 'Sharpe Ratio']])
    
    # 绘制回测结果
    bt.plot(superimpose=False)  # 禁用叠加，以便清晰显示月线
    
    return stats, bt


def main():
    """主函数"""
    args = parse_args()
    stats, bt = run_long_term_macd_strategy(args)
    
    # 确保目录存在
    os.makedirs('data/csv', exist_ok=True)
    
    # 保存回测结果到CSV
    result_df = pd.DataFrame([stats])
    result_df.to_csv(f'data/csv/long_term_macd_{args.symbol}_results.csv', index=False)
    print(f"\n回测结果已保存到 data/csv/long_term_macd_{args.symbol}_results.csv")


if __name__ == "__main__":
    main()
