#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
多周期策略
结合周线和月线数据进行交易决策
"""

import pandas as pd
import numpy as np
from backtesting import Strategy
from common.timeframe_utils import (
    resample_to_weekly,
    resample_to_monthly,
    map_higher_timeframe_to_daily
)
from common.indicators import calculate_ma


class MultiTimeframeStrategy(Strategy):
    """
    多周期策略
    
    使用周线和月线数据的组合进行交易决策：
    - 月线确定大趋势方向
    - 周线寻找入场点
    
    参数:
    - weekly_fast_ma: 周线短期均线周期
    - weekly_slow_ma: 周线长期均线周期
    - monthly_ma: 月线均线周期
    - stop_loss_pct: 止损百分比 (0.05 表示 5%)
    - take_profit_pct: 止盈百分比 (0.1 表示 10%)
    """
    # 定义策略参数
    weekly_fast_ma = 4  # 周线短期均线（约1个月）
    weekly_slow_ma = 10  # 周线长期均线（约2.5个月）
    monthly_ma = 6  # 月线均线（半年）
    stop_loss_pct = 0.05
    take_profit_pct = 0.1
    
    def init(self):
        """初始化策略，计算指标"""
        # 获取周线和月线数据
        self.weekly_data = resample_to_weekly(self.data.df.copy())
        self.monthly_data = resample_to_monthly(self.data.df.copy())
        
        # 计算周线指标
        self.weekly_fast = calculate_ma(self.weekly_data, self.weekly_fast_ma)
        self.weekly_slow = calculate_ma(self.weekly_data, self.weekly_slow_ma)
        
        # 计算月线指标
        self.monthly_ma_line = calculate_ma(self.monthly_data, self.monthly_ma)
        
        # 将计算结果添加到策略中
        self.weekly_fast_ma_line = self.I(map_higher_timeframe_to_daily, self.data.df, self.weekly_fast)
        self.weekly_slow_ma_line = self.I(map_higher_timeframe_to_daily, self.data.df, self.weekly_slow)
        self.monthly_ma_line_daily = self.I(map_higher_timeframe_to_daily, self.data.df, self.monthly_ma_line)
    
    def next(self):
        """每个新的K线数据到来时执行的逻辑"""
        price = self.data.Close[-1]  # 当前收盘价
        
        # 获取当前日期的指标值
        weekly_fast_val = self.weekly_fast_ma_line[-1]
        weekly_slow_val = self.weekly_slow_ma_line[-1]
        monthly_ma_val = self.monthly_ma_line_daily[-1]
        
        # 如果没有持仓，检查买入信号
        if not self.position:
            # 月线趋势向上（价格在月线均线之上）
            monthly_trend_up = price > monthly_ma_val
            
            # 周线金叉（短期均线上穿长期均线）
            weekly_crossover = (self.weekly_fast_ma_line[-2] < self.weekly_slow_ma_line[-2] and 
                               self.weekly_fast_ma_line[-1] > self.weekly_slow_ma_line[-1])
            
            # 买入条件：月线趋势向上 + 周线金叉
            if monthly_trend_up and weekly_crossover:
                # 计算止损和止盈价格
                stop_loss = price * (1 - self.stop_loss_pct)
                take_profit = price * (1 + self.take_profit_pct)
                
                # 买入，并设置止损和止盈
                self.buy(sl=stop_loss, tp=take_profit)
        
        # 如果有持仓，检查卖出信号
        elif self.position:
            # 月线趋势转向下（价格跌破月线均线）
            monthly_trend_down = price < monthly_ma_val
            
            # 周线死叉（短期均线下穿长期均线）
            weekly_crossunder = (self.weekly_fast_ma_line[-2] > self.weekly_slow_ma_line[-2] and 
                                self.weekly_fast_ma_line[-1] < self.weekly_slow_ma_line[-1])
            
            # 卖出条件：月线趋势向下 或 周线死叉
            if monthly_trend_down or weekly_crossunder:
                self.position.close()
