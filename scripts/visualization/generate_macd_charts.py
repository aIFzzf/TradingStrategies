#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成股票K线图和MACD指标HTML报告
参考长期MACD策略逻辑，重点关注上涨和下跌大趋势
"""

import os
import sys
import pandas as pd
import argparse
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import json

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backtest_engine import get_stock_data
from common.indicators import MACD, EMA, KDJ
from common.timeframe_utils import resample_to_weekly, resample_to_monthly


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='生成股票K线图和MACD指标HTML报告')
    parser.add_argument('--analysis_file', type=str, required=True,
                        help='分析结果CSV文件路径')
    parser.add_argument('--output', type=str, default='data/html/stock_macd_charts.html',
                        help='输出HTML文件路径')
    parser.add_argument('--days', type=int, default=365,
                        help='获取最近多少天的数据')
    parser.add_argument('--signal_only', action='store_true',
                        help='只显示有买入信号的股票')
    parser.add_argument('--uptrend_only', action='store_true',
                        help='只显示处于上涨大趋势的股票')
    
    return parser.parse_args()


def calculate_indicators(data):
    """
    计算各种技术指标
    
    参数:
    - data: DataFrame, 股票数据
    
    返回:
    - dict: 包含各种技术指标的字典
    """
    # 定义参数
    fast_period = 12
    slow_period = 26
    signal_period = 9
    kdj_k_period = 9
    kdj_d_period = 3
    kdj_j_period = 3
    ema_period = 20
    
    # 计算日线指标
    daily_ema20 = EMA(data['Close'], ema_period)
    
    # 计算周线数据
    weekly_data = resample_to_weekly(data)
    weekly_close = weekly_data['Close']
    weekly_high = weekly_data['High']
    weekly_low = weekly_data['Low']
    
    weekly_dif, weekly_dea, weekly_macd = MACD(
        weekly_close, fast_period, slow_period, signal_period
    )
    weekly_k, weekly_d, weekly_j = KDJ(
        weekly_high, weekly_low, weekly_close, 
        kdj_k_period, kdj_d_period, kdj_j_period
    )
    
    # 计算月线数据
    monthly_data = resample_to_monthly(data)
    monthly_close = monthly_data['Close']
    monthly_high = monthly_data['High']
    monthly_low = monthly_data['Low']
    
    monthly_dif, monthly_dea, monthly_macd = MACD(
        monthly_close, fast_period, slow_period, signal_period
    )
    monthly_k, monthly_d, monthly_j = KDJ(
        monthly_high, monthly_low, monthly_close, 
        kdj_k_period, kdj_d_period, kdj_j_period
    )
    
    # 将周线和月线数据映射到日线时间框架
    def map_to_daily(higher_tf_series, daily_index):
        result = pd.Series(index=daily_index, dtype=float)
        for date in daily_index:
            mask = higher_tf_series.index <= date
            if mask.any():
                last_value = higher_tf_series[mask].iloc[-1]
                result[date] = last_value
        return result.ffill()
    
    # 映射周线指标到日线
    daily_index = data.index
    weekly_dif_daily = map_to_daily(weekly_dif, daily_index)
    weekly_dea_daily = map_to_daily(weekly_dea, daily_index)
    weekly_macd_daily = map_to_daily(weekly_macd, daily_index)
    weekly_k_daily = map_to_daily(weekly_k, daily_index)
    weekly_d_daily = map_to_daily(weekly_d, daily_index)
    
    # 映射月线指标到日线
    monthly_dif_daily = map_to_daily(monthly_dif, daily_index)
    monthly_dea_daily = map_to_daily(monthly_dea, daily_index)
    monthly_macd_daily = map_to_daily(monthly_macd, daily_index)
    monthly_k_daily = map_to_daily(monthly_k, daily_index)
    monthly_d_daily = map_to_daily(monthly_d, daily_index)
    
    # 计算月线MACD的DIF斜率
    monthly_dif_slope = monthly_dif.diff()
    monthly_dif_slope_daily = map_to_daily(monthly_dif_slope, daily_index)
    
    # 判断大趋势
    in_uptrend = pd.Series(False, index=daily_index)
    in_downtrend = pd.Series(False, index=daily_index)
    
    # 计算月线KDJ金叉和死叉
    monthly_kd_diff = monthly_k - monthly_d
    monthly_kd_diff_daily = map_to_daily(monthly_kd_diff, daily_index)
    monthly_kd_diff_prev_daily = map_to_daily(monthly_kd_diff.shift(1), daily_index)
    
    # 判断月线KDJ金叉：K线上穿D线
    monthly_kdj_golden_cross = (monthly_kd_diff_daily > 0) & (monthly_kd_diff_prev_daily <= 0)
    
    # 判断月线KDJ死叉：K线下穿D线
    monthly_kdj_death_cross = (monthly_kd_diff_daily < 0) & (monthly_kd_diff_prev_daily >= 0)
    
    # 判断上涨大趋势
    for i in range(1, len(daily_index)):
        date = daily_index[i]
        prev_date = daily_index[i-1]
        
        # 默认继承前一天的趋势状态
        in_uptrend[date] = in_uptrend[prev_date]
        in_downtrend[date] = in_downtrend[prev_date]
        
        # 判断上涨大趋势
        if monthly_kdj_golden_cross[date]:
            # 月线KDJ金叉
            if monthly_macd_daily[date] > 0 and monthly_dif_slope_daily[date] > 0:
                # 月线MACD>0且DIF斜率向上
                in_uptrend[date] = True
                in_downtrend[date] = False
        
        # 判断下跌大趋势
        if monthly_kdj_death_cross[date]:
            # 月线KDJ死叉
            if monthly_dif_slope_daily[date] < 0:
                # 月线MACD DIF斜率向下
                in_downtrend[date] = True
                in_uptrend[date] = False
    
    # 返回所有指标
    return {
        'daily': {
            'ema20': daily_ema20
        },
        'weekly': {
            'dif': weekly_dif_daily,
            'dea': weekly_dea_daily,
            'macd': weekly_macd_daily,
            'k': weekly_k_daily,
            'd': weekly_d_daily
        },
        'monthly': {
            'dif': monthly_dif_daily,
            'dea': monthly_dea_daily,
            'macd': monthly_macd_daily,
            'k': monthly_k_daily,
            'd': monthly_d_daily,
            'dif_slope': monthly_dif_slope_daily
        },
        'trend': {
            'in_uptrend': in_uptrend,
            'in_downtrend': in_downtrend
        }
    }


def create_macd_chart(stock_data, indicators, title, height=900):
    """
    创建带有MACD指标的K线图
    
    参数:
    - stock_data: DataFrame, 股票数据
    - indicators: dict, 技术指标
    - title: str, 图表标题
    - height: int, 图表高度
    
    返回:
    - Figure: Plotly图表对象
    """
    # 创建子图，包含K线图、成交量、周线MACD和月线MACD
    fig = make_subplots(
        rows=4, 
        cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=(
            title, 
            "成交量", 
            "周线MACD", 
            "月线MACD和KDJ"
        )
    )
    
    # 添加K线图
    fig.add_trace(
        go.Candlestick(
            x=stock_data.index,
            open=stock_data['Open'],
            high=stock_data['High'],
            low=stock_data['Low'],
            close=stock_data['Close'],
            name='价格'
        ),
        row=1, col=1
    )
    
    # 添加EMA20均线
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=indicators['daily']['ema20'],
            name='EMA20',
            line=dict(color='purple', width=1)
        ),
        row=1, col=1
    )
    
    # 添加上涨和下跌大趋势背景
    for i in range(1, len(stock_data.index)):
        date = stock_data.index[i]
        if indicators['trend']['in_uptrend'][date]:
            fig.add_shape(
                type="rect",
                x0=stock_data.index[i-1],
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
        elif indicators['trend']['in_downtrend'][date]:
            fig.add_shape(
                type="rect",
                x0=stock_data.index[i-1],
                x1=date,
                y0=0,
                y1=1,
                xref="x",
                yref="paper",
                fillcolor="rgba(255,0,0,0.1)",
                opacity=0.5,
                layer="below",
                line_width=0,
                row=1, col=1
            )
    
    # 添加成交量
    colors = ['red' if row['Close'] >= row['Open'] else 'green' for _, row in stock_data.iterrows()]
    fig.add_trace(
        go.Bar(
            x=stock_data.index,
            y=stock_data['Volume'],
            marker_color=colors,
            name='成交量'
        ),
        row=2, col=1
    )
    
    # 添加周线MACD
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=indicators['weekly']['dif'],
            name='周线DIF',
            line=dict(color='blue', width=1)
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=indicators['weekly']['dea'],
            name='周线DEA',
            line=dict(color='red', width=1)
        ),
        row=3, col=1
    )
    
    # 添加周线MACD柱状图
    colors = ['red' if val >= 0 else 'green' for val in indicators['weekly']['macd']]
    fig.add_trace(
        go.Bar(
            x=stock_data.index,
            y=indicators['weekly']['macd'],
            marker_color=colors,
            name='周线MACD'
        ),
        row=3, col=1
    )
    
    # 添加月线MACD
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=indicators['monthly']['dif'],
            name='月线DIF',
            line=dict(color='blue', width=1)
        ),
        row=4, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=indicators['monthly']['dea'],
            name='月线DEA',
            line=dict(color='red', width=1)
        ),
        row=4, col=1
    )
    
    # 添加月线MACD柱状图
    colors = ['red' if val >= 0 else 'green' for val in indicators['monthly']['macd']]
    fig.add_trace(
        go.Bar(
            x=stock_data.index,
            y=indicators['monthly']['macd'],
            marker_color=colors,
            name='月线MACD'
        ),
        row=4, col=1
    )
    
    # 添加月线KDJ
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=indicators['monthly']['k'],
            name='月线K',
            line=dict(color='blue', width=1, dash='dot')
        ),
        row=4, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=stock_data.index,
            y=indicators['monthly']['d'],
            name='月线D',
            line=dict(color='red', width=1, dash='dot')
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


def generate_html_report(analysis_file, output_file, days=365, signal_only=False, uptrend_only=False):
    """
    生成HTML报告
    
    参数:
    - analysis_file: str, 分析结果CSV文件路径
    - output_file: str, 输出HTML文件路径
    - days: int, 获取最近多少天的数据
    - signal_only: bool, 是否只显示有买入信号的股票
    - uptrend_only: bool, 是否只显示处于上涨大趋势的股票
    """
    # 加载分析结果
    if not os.path.exists(analysis_file):
        print(f"分析结果文件不存在: {analysis_file}")
        return
    
    analysis_df = pd.read_csv(analysis_file)
    
    # 过滤股票
    if signal_only:
        analysis_df = analysis_df[analysis_df['Buy Signal'] == 'Yes']
    
    if uptrend_only:
        analysis_df = analysis_df[analysis_df['In Uptrend'] == 'Yes']
    
    if analysis_df.empty:
        print("没有符合条件的股票")
        return
    
    # 计算日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # 创建HTML文件内容
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>股票MACD分析报告</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
                border-radius: 5px;
            }}
            h1, h2 {{
                color: #333;
            }}
            .chart-container {{
                margin-bottom: 50px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
            .stock-info {{
                margin-bottom: 10px;
                padding: 10px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }}
            .buy-signal {{
                color: green;
                font-weight: bold;
            }}
            .uptrend {{
                color: blue;
                font-weight: bold;
            }}
            .date {{
                color: #666;
                font-size: 0.9em;
            }}
            .indicator-explanation {{
                margin-top: 10px;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>股票MACD分析报告</h1>
            <p class="date">生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>数据范围: {start_date} 至 {end_date}</p>
            <div class="indicator-explanation">
                <h3>长期MACD策略说明</h3>
                <p>本报告基于长期MACD策略，该策略主要关注上涨和下跌大趋势的判断。</p>
                <h4>上涨大趋势判断条件:</h4>
                <ul>
                    <li>月线KDJ金叉</li>
                    <li>月线MACD值>0</li>
                    <li>月线MACD DIF斜率向上</li>
                </ul>
                <h4>下跌大趋势判断条件:</h4>
                <ul>
                    <li>月线KDJ死叉</li>
                    <li>月线MACD DIF斜率向下</li>
                </ul>
                <h4>图表说明:</h4>
                <ul>
                    <li>K线图背景中，<span style="color:green">绿色区域</span>表示处于上涨大趋势，<span style="color:red">红色区域</span>表示处于下跌大趋势</li>
                </ul>
            </div>
    """
    
    # 获取每只股票的数据并创建图表
    for _, row in analysis_df.iterrows():
        symbol = row['Symbol']
        name = row['Name']
        price = row['Price']
        buy_signal = row['Buy Signal']
        in_uptrend = row['In Uptrend']
        
        print(f"处理 {symbol} - {name}...")
        
        try:
            # 获取股票数据
            stock_data = get_stock_data(symbol, start_date, end_date)
            
            if stock_data is None or stock_data.empty:
                print(f"无法获取 {symbol} 的数据，跳过")
                continue
            
            # 计算指标
            indicators = calculate_indicators(stock_data)
            
            # 创建图表
            title = f"{symbol} - {name}"
            fig = create_macd_chart(stock_data, indicators, title)
            
            # 添加股票信息和图表到HTML
            html_content += f"""
            <div class="chart-container">
                <div class="stock-info">
                    <h2>{symbol} - {name}</h2>
                    <p>当前价格: {price:.2f}</p>
                    <p>买入信号: <span class="{'buy-signal' if buy_signal == 'Yes' else ''}">{buy_signal}</span></p>
                    <p>上涨大趋势: <span class="{'uptrend' if in_uptrend == 'Yes' else ''}">{in_uptrend}</span></p>
                </div>
                {fig.to_html(full_html=False, include_plotlyjs=False)}
            </div>
            """
        except Exception as e:
            print(f"处理 {symbol} 时出错: {e}")
    
    # 完成HTML文件
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 保存HTML文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML报告已生成: {output_file}")


def main():
    """主函数"""
    args = parse_args()
    
    generate_html_report(
        args.analysis_file,
        args.output,
        args.days,
        args.signal_only,
        args.uptrend_only
    )


if __name__ == "__main__":
    main()
