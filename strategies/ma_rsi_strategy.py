#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高级交易策略：结合双均线和RSI指标
- 买入条件：短期均线上穿长期均线 AND RSI < 70 (非超买)
- 卖出条件：短期均线下穿长期均线 OR RSI > 80 (超买)
"""

import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover, TrailingStrategy
from common.indicators import SMA, RSI


class MACrossRSI(TrailingStrategy):
    """
    结合双均线和RSI的交易策略，同时使用跟踪止损
    
    参数:
    - fast_ma: 短期均线周期
    - slow_ma: 长期均线周期
    - rsi_period: RSI计算周期
    - rsi_buy_threshold: RSI买入阈值（低于此值视为超卖）
    - rsi_sell_threshold: RSI卖出阈值（高于此值视为超买）
    - trailing_sl_atr: 跟踪止损的ATR倍数
    """
    # 策略参数
    fast_ma = 10
    slow_ma = 30
    rsi_period = 14
    rsi_buy_threshold = 70  # 非超买
    rsi_sell_threshold = 80  # 超买
    trailing_sl_atr = 2.0  # 跟踪止损为2倍ATR
    
    def init(self):
        """初始化策略，计算指标"""
        # 必须调用父类的init方法
        super().init()
        
        # 获取价格数据
        price = self.data.Close
        
        # 计算移动平均线
        self.fast_ma_line = self.I(SMA, price, self.fast_ma)
        self.slow_ma_line = self.I(SMA, price, self.slow_ma)
        
        # 计算RSI指标
        self.rsi = self.I(RSI, price, self.rsi_period)
        
        # 设置跟踪止损
        self.set_trailing_sl(self.trailing_sl_atr)
    
    def next(self):
        """每个新的K线数据到来时执行的逻辑"""
        # 必须调用父类的next方法
        super().next()
        
        # 如果没有持仓，检查买入信号
        if not self.position:
            # 买入条件：短期均线上穿长期均线 AND RSI < rsi_buy_threshold (非超买)
            if crossover(self.fast_ma_line, self.slow_ma_line) and self.rsi[-1] < self.rsi_buy_threshold:
                self.buy()
        
        # 如果有持仓，检查卖出信号
        elif self.position:
            # 卖出条件：短期均线下穿长期均线 OR RSI > rsi_sell_threshold (超买)
            if crossover(self.slow_ma_line, self.fast_ma_line) or self.rsi[-1] > self.rsi_sell_threshold:
                self.position.close()
