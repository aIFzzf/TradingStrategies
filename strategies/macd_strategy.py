#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MACD交易策略
基于MACD指标的金叉和死叉信号
"""

import pandas as pd
import numpy as np
from backtesting import Strategy


class MACDStrategy(Strategy):
    """
    MACD交易策略
    
    参数:
    - fast_period: 快速EMA周期
    - slow_period: 慢速EMA周期
    - signal_period: 信号线周期
    - stop_loss_pct: 止损百分比 (0.05 表示 5%)
    - take_profit_pct: 止盈百分比 (0.1 表示 10%)
    """
    # 定义策略参数
    fast_period = 12
    slow_period = 26
    signal_period = 9
    stop_loss_pct = 0.05
    take_profit_pct = 0.1
    
    def init(self):
        """初始化策略，计算指标"""
        # 获取收盘价
        close = self.data.Close
        
        # 计算MACD指标
        self.macd_line, self.signal_line, self.histogram = self.I(
            self.MACD, close, self.fast_period, self.slow_period, self.signal_period
        )
    
    def next(self):
        """每个新的K线数据到来时执行的逻辑"""
        price = self.data.Close[-1]  # 当前收盘价
        
        # 如果没有持仓，检查买入信号
        if not self.position:
            # 当MACD线上穿信号线时买入（金叉）
            if self.macd_line[-2] < self.signal_line[-2] and self.macd_line[-1] > self.signal_line[-1]:
                # 计算止损和止盈价格
                stop_loss = price * (1 - self.stop_loss_pct)
                take_profit = price * (1 + self.take_profit_pct)
                
                # 买入，并设置止损和止盈
                self.buy(sl=stop_loss, tp=take_profit)
        
        # 如果有持仓，检查卖出信号
        elif self.position:
            # 当MACD线下穿信号线时卖出（死叉）
            if self.macd_line[-2] > self.signal_line[-2] and self.macd_line[-1] < self.signal_line[-1]:
                self.position.close()
    
    @staticmethod
    def MACD(values, fast_period, slow_period, signal_period):
        """
        计算MACD指标
        
        参数:
        - values: 价格序列
        - fast_period: 快速EMA周期
        - slow_period: 慢速EMA周期
        - signal_period: 信号线周期
        
        返回:
        - macd_line: MACD线 (快速EMA - 慢速EMA)
        - signal_line: 信号线 (MACD的EMA)
        - histogram: 柱状图 (MACD线 - 信号线)
        """
        # 转换为pandas Series
        close = pd.Series(values)
        
        # 计算快速和慢速EMA
        fast_ema = close.ewm(span=fast_period, adjust=False).mean()
        slow_ema = close.ewm(span=slow_period, adjust=False).mean()
        
        # 计算MACD线
        macd_line = fast_ema - slow_ema
        
        # 计算信号线
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # 计算柱状图
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
