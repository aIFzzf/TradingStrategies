#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行交易策略示例
"""

import argparse
import pandas as pd
import os
from strategies import DualMAStrategy, MACrossRSI, BollingerBandStrategy, MACDStrategy, MultiTimeframeStrategy, LongTermMACDStrategy
from backtest_engine import (
    get_stock_data, 
    run_backtest, 
    optimize_strategy, 
    compare_strategies,
    plot_equity_curves,
    resample_data
)
from common.timeframe_utils import resample_to_timeframe, get_timeframe_data
from analysis import analyze_strategy_results, compare_strategies as compare_strategy_results, batch_analyze_all_results

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='运行交易策略回测')
    
    parser.add_argument('--symbol', type=str, default='AAPL',
                        help='股票代码，例如 AAPL')
    
    parser.add_argument('--start', type=str, default='2020-01-01',
                        help='开始日期，格式 YYYY-MM-DD')
    
    parser.add_argument('--end', type=str, default='2023-12-31',
                        help='结束日期，格式 YYYY-MM-DD')
    
    parser.add_argument('--interval', type=str, default='1d',
                        choices=['1d', '1wk', '1mo'],
                        help='数据周期: 1d(日线), 1wk(周线), 1mo(月线)')
    
    parser.add_argument('--strategy', type=str, default='dual_ma',
                        choices=['dual_ma', 'ma_rsi', 'bollinger', 'macd', 'multi_tf', 'long_term_macd', 'compare'],
                        help='要运行的策略类型')
    
    parser.add_argument('--optimize', action='store_true',
                        help='是否优化策略参数')
    
    parser.add_argument('--fast_ma', type=int, default=10,
                        help='短期均线周期')
    
    parser.add_argument('--slow_ma', type=int, default=30,
                        help='长期均线周期')
    
    parser.add_argument('--stop_loss', type=float, default=0.05,
                        help='止损百分比')
    
    parser.add_argument('--take_profit', type=float, default=0.1,
                        help='止盈百分比')
    
    # 布林带策略参数
    parser.add_argument('--bb_period', type=int, default=20,
                        help='布林带周期')
    
    parser.add_argument('--bb_std', type=float, default=2.0,
                        help='布林带标准差倍数')
    
    # MACD策略参数
    parser.add_argument('--fast_period', type=int, default=12,
                        help='MACD快线周期')
    
    parser.add_argument('--slow_period', type=int, default=26,
                        help='MACD慢线周期')
    
    parser.add_argument('--signal_period', type=int, default=9,
                        help='MACD信号线周期')
    
    # 多周期策略参数
    parser.add_argument('--weekly_fast_ma', type=int, default=4,
                        help='周线短期均线周期')
    
    parser.add_argument('--weekly_slow_ma', type=int, default=10,
                        help='周线长期均线周期')
    
    parser.add_argument('--monthly_ma', type=int, default=6,
                        help='月线均线周期')
    
    # 长期MACD策略参数
    parser.add_argument('--ema_period', type=int, default=20,
                        help='日线EMA周期')
    
    parser.add_argument('--price_range_pct', type=float, default=0.05,
                        help='筹码集中区域上下浮动百分比')
    
    parser.add_argument('--position_size', type=float, default=1.0,
                        help='仓位大小，范围0.0-1.0，默认1.0表示全仓')
    
    parser.add_argument('--downtrend_exit_size', type=float, default=0.5,
                        help='趋势反转时卖出的仓位比例，范围0.0-1.0，默认0.5表示卖出一半')
    
    # 分析报表相关参数
    parser.add_argument('--generate_report', action='store_true',
                        help='是否生成分析报表')
    
    parser.add_argument('--compare_report', action='store_true',
                        help='是否生成策略比较报表')
    
    parser.add_argument('--batch_analyze', action='store_true',
                        help='批量分析所有回测结果并生成报表')
    
    parser.add_argument('--report_metric', type=str, default='Return [%]',
                        choices=['Return [%]', 'Max. Drawdown [%]', 'Sharpe Ratio', '# Trades', 'Win Rate [%]'],
                        help='策略比较报表中使用的指标')
    
    return parser.parse_args()


def run_dual_ma_strategy(data, args, optimize=False):
    """运行双均线策略"""
    if optimize:
        print(f"优化双均线策略参数...")
        optimization_params = {
            'fast_ma': range(5, 21, 5),
            'slow_ma': range(20, 61, 10),
            'stop_loss_pct': [0.03, 0.05, 0.07],
            'take_profit_pct': [0.08, 0.1, 0.15]
        }
        
        constraint = lambda p: p.fast_ma < p.slow_ma
        
        stats, bt = optimize_strategy(
            data, 
            DualMAStrategy, 
            optimization_params, 
            maximize='Return [%]',
            constraint=constraint
        )
        
        print("\n最优参数:")
        print(f"快速均线周期: {stats._strategy.fast_ma}")
        print(f"慢速均线周期: {stats._strategy.slow_ma}")
        print(f"止损百分比: {stats._strategy.stop_loss_pct}")
        print(f"止盈百分比: {stats._strategy.take_profit_pct}")
        
        # 使用最优参数运行回测
        params = {
            'fast_ma': stats._strategy.fast_ma,
            'slow_ma': stats._strategy.slow_ma,
            'stop_loss_pct': stats._strategy.stop_loss_pct,
            'take_profit_pct': stats._strategy.take_profit_pct
        }
    else:
        params = {
            'fast_ma': args.fast_ma,
            'slow_ma': args.slow_ma,
            'stop_loss_pct': args.stop_loss,
            'take_profit_pct': args.take_profit
        }
    
    print(f"运行双均线策略，参数: {params}")
    stats, bt = run_backtest(data, DualMAStrategy, **params)
    
    print("\n回测结果:")
    print(stats)
    
    # 绘制回测结果
    bt.plot()
    
    return stats, bt


def run_ma_rsi_strategy(data, args, optimize=False):
    """运行MA+RSI策略"""
    if optimize:
        print(f"优化MA+RSI策略参数...")
        optimization_params = {
            'fast_ma': range(5, 21, 5),
            'slow_ma': range(20, 61, 10),
            'rsi_period': [7, 14, 21],
            'rsi_buy_threshold': [60, 70, 80],
            'rsi_sell_threshold': [70, 80, 90],
            'trailing_sl_atr': [1.5, 2.0, 2.5]
        }
        
        constraint = lambda p: p.fast_ma < p.slow_ma and p.rsi_buy_threshold < p.rsi_sell_threshold
        
        stats, bt = optimize_strategy(
            data, 
            MACrossRSI, 
            optimization_params, 
            maximize='Sharpe Ratio',
            constraint=constraint
        )
        
        print("\n最优参数:")
        print(f"快速均线周期: {stats._strategy.fast_ma}")
        print(f"慢速均线周期: {stats._strategy.slow_ma}")
        print(f"RSI周期: {stats._strategy.rsi_period}")
        print(f"RSI买入阈值: {stats._strategy.rsi_buy_threshold}")
        print(f"RSI卖出阈值: {stats._strategy.rsi_sell_threshold}")
        print(f"跟踪止损ATR倍数: {stats._strategy.trailing_sl_atr}")
        
        # 使用最优参数运行回测
        params = {
            'fast_ma': stats._strategy.fast_ma,
            'slow_ma': stats._strategy.slow_ma,
            'rsi_period': stats._strategy.rsi_period,
            'rsi_buy_threshold': stats._strategy.rsi_buy_threshold,
            'rsi_sell_threshold': stats._strategy.rsi_sell_threshold,
            'trailing_sl_atr': stats._strategy.trailing_sl_atr
        }
    else:
        params = {
            'fast_ma': args.fast_ma,
            'slow_ma': args.slow_ma
        }
    
    print(f"运行MA+RSI策略，参数: {params}")
    stats, bt = run_backtest(data, MACrossRSI, **params)
    
    print("\n回测结果:")
    print(stats)
    
    # 绘制回测结果
    bt.plot()
    
    return stats, bt


def run_bollinger_strategy(data, args, optimize=False):
    """运行布林带策略"""
    if optimize:
        print(f"优化布林带策略参数...")
        optimization_params = {
            'bb_period': range(10, 31, 5),
            'bb_std': [1.5, 2.0, 2.5, 3.0],
            'stop_loss_pct': [0.03, 0.05, 0.07]
        }
        
        stats, bt = optimize_strategy(
            data, 
            BollingerBandStrategy, 
            optimization_params, 
            maximize='Return [%]'
        )
        
        print("\n最优参数:")
        print(f"布林带周期: {stats._strategy.bb_period}")
        print(f"布林带标准差倍数: {stats._strategy.bb_std}")
        print(f"止损百分比: {stats._strategy.stop_loss_pct}")
        
        # 使用最优参数运行回测
        params = {
            'bb_period': stats._strategy.bb_period,
            'bb_std': stats._strategy.bb_std,
            'stop_loss_pct': stats._strategy.stop_loss_pct
        }
    else:
        params = {
            'bb_period': args.bb_period,
            'bb_std': args.bb_std,
            'stop_loss_pct': args.stop_loss
        }
    
    print(f"运行布林带策略，参数: {params}")
    stats, bt = run_backtest(data, BollingerBandStrategy, **params)
    
    print("\n回测结果:")
    print(stats)
    
    # 绘制回测结果
    bt.plot()
    
    return stats, bt


def run_macd_strategy(data, args, optimize=False):
    """运行MACD策略"""
    if optimize:
        print(f"优化MACD策略参数...")
        optimization_params = {
            'fast_period': range(8, 17, 2),
            'slow_period': range(20, 31, 2),
            'signal_period': range(7, 12, 1),
            'stop_loss_pct': [0.03, 0.05, 0.07],
            'take_profit_pct': [0.08, 0.1, 0.15]
        }
        
        constraint = lambda p: p.fast_period < p.slow_period
        
        stats, bt = optimize_strategy(
            data, 
            MACDStrategy, 
            optimization_params, 
            maximize='Return [%]',
            constraint=constraint
        )
        
        print("\n最优参数:")
        print(f"快线周期: {stats._strategy.fast_period}")
        print(f"慢线周期: {stats._strategy.slow_period}")
        print(f"信号线周期: {stats._strategy.signal_period}")
        print(f"止损百分比: {stats._strategy.stop_loss_pct}")
        print(f"止盈百分比: {stats._strategy.take_profit_pct}")
        
        # 使用最优参数运行回测
        params = {
            'fast_period': stats._strategy.fast_period,
            'slow_period': stats._strategy.slow_period,
            'signal_period': stats._strategy.signal_period,
            'stop_loss_pct': stats._strategy.stop_loss_pct,
            'take_profit_pct': stats._strategy.take_profit_pct
        }
    else:
        params = {
            'fast_period': args.fast_period,
            'slow_period': args.slow_period,
            'signal_period': args.signal_period,
            'stop_loss_pct': args.stop_loss,
            'take_profit_pct': args.take_profit
        }
    
    print(f"运行MACD策略，参数: {params}")
    stats, bt = run_backtest(data, MACDStrategy, **params)
    
    print("\n回测结果:")
    print(stats)
    
    # 绘制回测结果
    bt.plot()
    
    return stats, bt


def run_multi_tf_strategy(data, args, optimize=False):
    """运行多周期策略"""
    print(f"运行多周期策略，参数: {{'weekly_fast_ma': 4, 'weekly_slow_ma': 10, 'monthly_ma': 6, 'stop_loss_pct': 0.05, 'take_profit_pct': 0.1}}")
    
    # 默认参数
    params = {}
    
    # 如果需要优化
    if optimize:
        print("优化多周期策略参数...")
        
        # 定义参数范围
        params_dict = {
            'weekly_fast_ma': range(2, 10, 2),
            'weekly_slow_ma': range(8, 20, 2),
            'monthly_ma': range(3, 12, 3),
            'stop_loss_pct': [0.03, 0.05, 0.07],
            'take_profit_pct': [0.08, 0.1, 0.15]
        }
        
        # 运行优化
        stats, bt = optimize_strategy(data, MultiTimeframeStrategy, params_dict)
        
        # 打印优化结果
        print("\n优化结果:")
        print(f"最佳参数: {stats._strategy}")
        print(f"回报率: {stats['Return [%]']:.2f}%")
        print(f"最大回撤: {stats['Max. Drawdown [%]']:.2f}%")
        print(f"夏普比率: {stats['Sharpe Ratio']:.2f}")
        
        # 绘制回测结果
        bt.plot()
    else:
        # 使用默认参数运行策略
        stats, bt = run_backtest(data, MultiTimeframeStrategy)
        
        # 打印回测结果
        print("\n回测结果:")
        print(f"回报率: {stats['Return [%]']:.2f}%")
        print(f"买入持有回报率: {stats['Buy & Hold Return [%]']:.2f}%")
        print(f"最大回撤: {stats['Max. Drawdown [%]']:.2f}%")
        print(f"交易次数: {stats['# Trades']}")
        print(f"胜率: {stats['Win Rate [%]']:.2f}%")
        print(f"夏普比率: {stats['Sharpe Ratio']:.2f}")
        
        # 绘制回测结果
        bt.plot()
        
    return stats, bt


def run_long_term_macd_strategy(data, args, optimize=False):
    """运行长期MACD策略"""
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
    
    # 运行回测
    stats, bt = run_backtest(data, strategy)
    
    print("\n回测结果:")
    print(stats[['Start', 'End', 'Duration', 'Return [%]', 'Max. Drawdown [%]', 
                 '# Trades', 'Win Rate [%]', 'Sharpe Ratio']])
    
    # 绘制回测结果
    bt.plot(superimpose=False)  # 禁用叠加，以便清晰显示
    
    # 确保目录存在
    os.makedirs('data/csv', exist_ok=True)
    
    # 保存回测结果到CSV
    result_df = pd.DataFrame([stats])
    result_df.to_csv(f'data/csv/long_term_macd_{args.symbol}_results.csv', index=False)
    print(f"\n回测结果已保存到 data/csv/long_term_macd_{args.symbol}_results.csv")
    
    return stats, bt


def run_strategy_comparison(data, args):
    """比较不同策略"""
    print("比较不同策略的表现...")
    
    # 双均线策略
    dual_ma_params = {
        'fast_ma': args.fast_ma,
        'slow_ma': args.slow_ma,
        'stop_loss_pct': args.stop_loss,
        'take_profit_pct': args.take_profit
    }
    
    # MA+RSI策略
    ma_rsi_params = {
        'fast_ma': args.fast_ma,
        'slow_ma': args.slow_ma,
        'rsi_period': 14,
        'rsi_buy_threshold': 30,
        'rsi_sell_threshold': 70,
        'trailing_sl_atr': 2.0
    }
    
    # 布林带策略
    bollinger_params = {
        'bb_period': args.bb_period,
        'bb_std': args.bb_std,
        'stop_loss_pct': args.stop_loss
    }
    
    # MACD策略
    macd_params = {
        'fast_period': args.fast_period,
        'slow_period': args.slow_period,
        'signal_period': args.signal_period,
        'stop_loss_pct': args.stop_loss,
        'take_profit_pct': args.take_profit
    }
    
    # 多周期策略
    multi_tf_params = {
        'weekly_fast_ma': args.weekly_fast_ma,
        'weekly_slow_ma': args.weekly_slow_ma,
        'monthly_ma': args.monthly_ma,
        'stop_loss_pct': args.stop_loss,
        'take_profit_pct': args.take_profit
    }
    
    # 长期MACD策略参数
    long_term_macd_params = {
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
    
    # 确保使用日线数据
    daily_data = data
    if args.interval != '1d':
        print("获取日线数据用于多周期策略...")
        daily_data = get_stock_data(args.symbol, args.start, args.end, interval='1d')
    
    # 运行各个策略
    print("运行双均线策略...")
    dual_ma_stats, dual_ma_bt = run_backtest(data, DualMAStrategy, **dual_ma_params)
    
    print("运行MA+RSI策略...")
    ma_rsi_stats, ma_rsi_bt = run_backtest(data, MACrossRSI, **ma_rsi_params)
    
    print("运行布林带策略...")
    bollinger_stats, bollinger_bt = run_backtest(data, BollingerBandStrategy, **bollinger_params)
    
    print("运行MACD策略...")
    macd_stats, macd_bt = run_backtest(data, MACDStrategy, **macd_params)
    
    print("运行多周期策略...")
    multi_tf_stats, multi_tf_bt = run_backtest(daily_data, MultiTimeframeStrategy)
    
    print("运行长期MACD策略...")
    # 获取月线数据用于长期MACD策略
    monthly_data = resample_data(data, interval='M')
    long_term_macd_stats, long_term_macd_bt = run_backtest(monthly_data, LongTermMACDStrategy, **long_term_macd_params)
    
    # 比较结果
    strategies = {
        '双均线策略': dual_ma_bt,
        'MA+RSI策略': ma_rsi_bt,
        '布林带策略': bollinger_bt,
        'MACD策略': macd_bt,
        '多周期策略': multi_tf_bt,
        '长期MACD策略': long_term_macd_bt
    }
    
    # 绘制权益曲线对比
    plot_equity_curves(strategies)
    
    # 打印性能指标对比
    print("\n策略性能对比:")
    comparison = pd.DataFrame({
        '双均线策略': dual_ma_stats,
        'MA+RSI策略': ma_rsi_stats,
        '布林带策略': bollinger_stats,
        'MACD策略': macd_stats,
        '多周期策略': multi_tf_stats,
        '长期MACD策略': long_term_macd_stats
    })
    print(comparison)


def main():
    """主函数"""
    args = parse_args()
    
    # 获取股票数据
    print(f"获取 {args.symbol} 的股票数据，从 {args.start} 到 {args.end}，周期: {args.interval}")
    data = get_stock_data(args.symbol, args.start, args.end, interval=args.interval)
    
    # 根据策略类型运行相应的策略
    if args.strategy == 'dual_ma':
        run_dual_ma_strategy(data, args, optimize=args.optimize)
        if args.generate_report:
            print(f"生成双均线策略分析报表...")
            report_path = analyze_strategy_results('dual_ma', args.symbol)
            print(f"报表已生成: {report_path}")
    elif args.strategy == 'ma_rsi':
        run_ma_rsi_strategy(data, args, optimize=args.optimize)
        if args.generate_report:
            print(f"生成MA+RSI策略分析报表...")
            report_path = analyze_strategy_results('ma_rsi', args.symbol)
            print(f"报表已生成: {report_path}")
    elif args.strategy == 'bollinger':
        run_bollinger_strategy(data, args, optimize=args.optimize)
        if args.generate_report:
            print(f"生成布林带策略分析报表...")
            report_path = analyze_strategy_results('bollinger', args.symbol)
            print(f"报表已生成: {report_path}")
    elif args.strategy == 'macd':
        run_macd_strategy(data, args, optimize=args.optimize)
        if args.generate_report:
            print(f"生成MACD策略分析报表...")
            report_path = analyze_strategy_results('macd', args.symbol)
            print(f"报表已生成: {report_path}")
    elif args.strategy == 'multi_tf':
        run_multi_tf_strategy(data, args, optimize=args.optimize)
        if args.generate_report:
            print(f"生成多周期策略分析报表...")
            report_path = analyze_strategy_results('multi_tf', args.symbol)
            print(f"报表已生成: {report_path}")
    elif args.strategy == 'long_term_macd':
        # 对于长期MACD策略，我们使用月线数据
        monthly_data = resample_data(data, interval='M')
        run_long_term_macd_strategy(monthly_data, args, optimize=args.optimize)
        if args.generate_report:
            print(f"生成长期MACD策略分析报表...")
            report_path = analyze_strategy_results('long_term_macd', args.symbol)
            print(f"报表已生成: {report_path}")
    elif args.strategy == 'compare':
        run_strategy_comparison(data, args)
        if args.compare_report:
            print(f"生成策略比较报表...")
            strategies = ['dual_ma', 'ma_rsi', 'bollinger', 'macd', 'multi_tf', 'long_term_macd']
            report_path = compare_strategy_results(strategies, args.symbol, metric=args.report_metric)
            print(f"比较报表已生成: {report_path}")
    
    # 批量分析所有回测结果
    if args.batch_analyze:
        print("批量分析所有回测结果...")
        report_paths = batch_analyze_all_results()
        print(f"已生成 {len(report_paths)} 个策略报表")


if __name__ == "__main__":
    main()
