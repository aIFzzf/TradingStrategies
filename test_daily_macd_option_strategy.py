#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试日线MACD期权策略
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backtest_engine import get_stock_data
from strategies.daily_macd_option_strategy import DailyMACDOptionStrategy
from common.indicators import MACD, EMA


def parse_args():
    """解析命令行参数"""
    import argparse
    parser = argparse.ArgumentParser(description='测试日线MACD期权策略')
    parser.add_argument('--symbol', type=str, default='AAPL',
                        help='股票代码')
    parser.add_argument('--start_date', type=str, 
                        default=(datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                        help='开始日期')
    parser.add_argument('--end_date', type=str, 
                        default=datetime.now().strftime('%Y-%m-%d'),
                        help='结束日期')
    parser.add_argument('--lookback_days', type=int, default=30,
                        help='往前查找的天数')
    parser.add_argument('--output', type=str, default='data/html',
                        help='输出目录')
    return parser.parse_args()


def test_strategy(symbol, start_date, end_date, lookback_days=30, output_dir='data/html'):
    """
    测试日线MACD期权策略
    
    参数:
    - symbol: str, 股票代码
    - start_date: str, 开始日期
    - end_date: str, 结束日期
    - lookback_days: int, 往前查找的天数
    - output_dir: str, 输出目录
    """
    print(f"测试股票: {symbol}")
    print(f"时间范围: {start_date} 至 {end_date}")
    print(f"查找天数: {lookback_days}天\n")
    
    # 获取股票数据
    data = get_stock_data(symbol, start_date, end_date)
    if data is None or len(data) == 0:
        print(f"无法获取股票 {symbol} 的数据")
        return
    
    print(f"获取到 {len(data)} 条数据")
    
    # 计算指标
    indicators = DailyMACDOptionStrategy.calculate_trend_indicators(data, lookback_days)
    
    # 计算买卖点
    buy_signals = []
    sell_signals = []
    
    # 遍历每一天，找出买卖点
    for i in range(lookback_days, len(data)-1):
        current_date = data.index[i]
        next_date = data.index[i+1]
        
        # 当前日期不在上升趋势，下一个日期在上升趋势 -> 买入信号
        if not indicators['trend']['in_uptrend'][current_date] and indicators['trend']['in_uptrend'][next_date]:
            buy_signals.append((next_date, data['Close'][next_date]))
        
        # 当前日期在上升趋势，下一个日期不在上升趋势 -> 卖出信号
        if indicators['trend']['in_uptrend'][current_date] and not indicators['trend']['in_uptrend'][next_date]:
            sell_signals.append((next_date, data['Close'][next_date]))
    
    # 获取最新的信号
    latest_signal = DailyMACDOptionStrategy.judge_signals(data, indicators, lookback_days)
    
    print("\n最新信号:")
    print(f"日期: {latest_signal['date'].strftime('%Y-%m-%d')}")
    print(f"上升趋势: {'是' if latest_signal['in_uptrend'] else '否'}")
    print(f"买入信号: {'是' if latest_signal['buy_signal'] else '否'}")
    print(f"卖出信号: {'是' if latest_signal['sell_signal'] else '否'}")
    
    # 统计上升趋势的天数
    uptrend_days = indicators['trend']['in_uptrend'].sum()
    total_days = len(indicators['trend']['in_uptrend'])
    uptrend_percentage = uptrend_days / total_days * 100 if total_days > 0 else 0
    
    print(f"\n上升趋势天数: {uptrend_days} / {total_days} ({uptrend_percentage:.2f}%)")
    
    # 计算策略收益
    if len(buy_signals) > 0 and len(sell_signals) > 0:
        returns = []
        positions = []
        current_position = None
        
        for i, row in data.iterrows():
            # 检查是否有买入信号
            for date, price in buy_signals:
                if i == date and current_position is None:
                    current_position = price
                    positions.append((i, price, 'buy'))
            
            # 检查是否有卖出信号
            for date, price in sell_signals:
                if i == date and current_position is not None:
                    returns.append((price / current_position - 1) * 100)
                    current_position = None
                    positions.append((i, price, 'sell'))
        
        if len(returns) > 0:
            avg_return = np.mean(returns)
            total_return = (1 + np.array(returns) / 100).prod() - 1
            total_return_pct = total_return * 100
            
            print(f"\n策略收益:")
            print(f"交易次数: {len(returns)}")
            print(f"平均收益率: {avg_return:.2f}%")
            print(f"总收益率: {total_return_pct:.2f}%")
    
    # 创建HTML图表
    fig = create_macd_chart(data, indicators, buy_signals, sell_signals, symbol)
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 保存HTML文件
    html_file = f"{output_dir}/{symbol}_daily_macd_option_strategy.html"
    fig.write_html(html_file)
    print(f"\nHTML图表已保存至: {html_file}")
    
    return indicators, latest_signal, buy_signals, sell_signals


def create_macd_chart(data, indicators, buy_signals, sell_signals, title, height=900):
    """
    创建带有MACD指标的K线图
    
    参数:
    - data: DataFrame, 股票数据
    - indicators: dict, 技术指标
    - buy_signals: list, 买入信号列表，每个元素为(日期, 价格)
    - sell_signals: list, 卖出信号列表，每个元素为(日期, 价格)
    - title: str, 图表标题
    - height: int, 图表高度
    
    返回:
    - Figure: Plotly图表对象
    """
    # 创建子图，包含K线图、成交量、MACD和趋势指标
    fig = make_subplots(
        rows=4, 
        cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=(
            f"{title} - 日线MACD期权策略", 
            "成交量", 
            "MACD指标", 
            "趋势指标"
        )
    )
    
    # 添加K线图
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='价格'
        ),
        row=1, col=1
    )
    
    # 添加EMA20均线
    ema20 = EMA(data['Close'], 20)
    fig.add_trace(
        go.Scatter(
            x=data.index[-len(ema20):],
            y=ema20,
            name='EMA20',
            line=dict(color='purple', width=1)
        ),
        row=1, col=1
    )
    
    # 添加上涨趋势背景
    for i in range(1, len(data.index)):
        date = data.index[i]
        if date in indicators['trend']['in_uptrend'].index and indicators['trend']['in_uptrend'][date]:
            fig.add_shape(
                type="rect",
                x0=data.index[i-1],
                x1=date,
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                fillcolor="rgba(0,255,0,0.1)",
                opacity=0.5,
                layer="below",
                line_width=0,
                row=1, col=1
            )
    
    # 添加买入点
    if buy_signals:
        buy_dates = [date for date, _ in buy_signals]
        buy_prices = [price for _, price in buy_signals]
        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode='markers',
                marker=dict(
                    symbol='triangle-up',
                    size=12,
                    color='green',
                    line=dict(color='black', width=1)
                ),
                name='买入信号'
            ),
            row=1, col=1
        )
    
    # 添加卖出点
    if sell_signals:
        sell_dates = [date for date, _ in sell_signals]
        sell_prices = [price for _, price in sell_signals]
        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode='markers',
                marker=dict(
                    symbol='triangle-down',
                    size=12,
                    color='red',
                    line=dict(color='black', width=1)
                ),
                name='卖出信号'
            ),
            row=1, col=1
        )
    
    # 添加成交量
    colors = ['red' if row['Close'] >= row['Open'] else 'green' for _, row in data.iterrows()]
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            marker_color=colors,
            name='成交量'
        ),
        row=2, col=1
    )
    
    # 添加MACD
    # 确保指标数据与原始数据长度匹配
    dif_values = indicators['daily']['dif']
    dea_values = indicators['daily']['dea']
    macd_values = indicators['daily']['macd']
    
    # 获取共同的索引
    common_index = data.index.intersection(dif_values.index)
    
    fig.add_trace(
        go.Scatter(
            x=common_index,
            y=dif_values[common_index],
            name='DIF',
            line=dict(color='blue', width=1)
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=common_index,
            y=dea_values[common_index],
            name='DEA',
            line=dict(color='red', width=1)
        ),
        row=3, col=1
    )
    
    # 添加MACD柱状图
    colors = ['red' if x >= 0 else 'green' for x in macd_values[common_index]]
    fig.add_trace(
        go.Bar(
            x=common_index,
            y=macd_values[common_index],
            marker_color=colors,
            name='MACD'
        ),
        row=3, col=1
    )
    
    # 标记MACD金叉和死叉
    macd_cross_dates = []
    macd_cross_values = []
    macd_cross_colors = []
    
    for i in range(1, len(common_index)):
        current_date = common_index[i]
        prev_date = common_index[i-1]
        
        current_dif = dif_values[current_date]
        current_dea = dea_values[current_date]
        prev_dif = dif_values[prev_date]
        prev_dea = dea_values[prev_date]
        
        # MACD金叉
        if current_dif > current_dea and prev_dif <= prev_dea:
            macd_cross_dates.append(current_date)
            macd_cross_values.append(current_dif)
            macd_cross_colors.append('green')
        
        # MACD死叉
        if current_dif < current_dea and prev_dif >= prev_dea:
            macd_cross_dates.append(current_date)
            macd_cross_values.append(current_dif)
            macd_cross_colors.append('red')
    
    fig.add_trace(
        go.Scatter(
            x=macd_cross_dates,
            y=macd_cross_values,
            mode='markers',
            marker=dict(
                color=macd_cross_colors,
                size=8,
                line=dict(color='black', width=1)
            ),
            name='MACD交叉'
        ),
        row=3, col=1
    )
    
    # 添加趋势指标
    fig.add_trace(
        go.Scatter(
            x=indicators['trend']['in_uptrend'].index,
            y=indicators['trend']['in_uptrend'],
            name='上升趋势',
            line=dict(color='green', width=1)
        ),
        row=4, col=1
    )
    
    # 更新布局
    fig.update_layout(
        height=height,
        xaxis_rangeslider_visible=False,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    
    # 更新X轴
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # 隐藏周末
        ]
    )
    
    return fig


if __name__ == "__main__":
    args = parse_args()
    test_strategy(args.symbol, args.start_date, args.end_date, args.lookback_days, args.output)
