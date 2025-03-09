#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
布林带交易策略
当价格触及下轨时买入，当价格触及上轨时卖出
"""

import pandas as pd
import numpy as np
from backtesting import Strategy


class BollingerBandStrategy(Strategy):
    """
    布林带交易策略
    
    参数:
    - bb_period: 布林带计算周期
    - bb_std: 布林带标准差倍数
    - stop_loss_pct: 止损百分比 (0.05 表示 5%)
    """
    # 定义策略参数
    bb_period = 20
    bb_std = 2.0
    stop_loss_pct = 0.05
    
    def init(self):
        """初始化策略，计算指标"""
        # 获取收盘价
        close = self.data.Close
        
        # 计算布林带
        self.sma = self.I(self.SMA, close, self.bb_period)
        self.upper = self.I(self.upper_band, close, self.sma, self.bb_std)
        self.lower = self.I(self.lower_band, close, self.sma, self.bb_std)
    
    def next(self):
        """每个新的K线数据到来时执行的逻辑"""
        price = self.data.Close[-1]  # 当前收盘价
        
        # 如果没有持仓，检查买入信号
        if not self.position:
            # 当价格触及下轨时买入
            if price <= self.lower[-1]:
                # 计算止损价格
                stop_loss = price * (1 - self.stop_loss_pct)
                
                # 买入，并设置止损
                self.buy(sl=stop_loss)
        
        # 如果有持仓，检查卖出信号
        elif self.position:
            # 当价格触及上轨时卖出
            if price >= self.upper[-1]:
                self.position.close()
    
    @staticmethod
    def SMA(values, n):
        """计算简单移动平均线"""
        return pd.Series(values).rolling(n).mean()
    
    @staticmethod
    def upper_band(values, sma, std_dev):
        """计算布林带上轨"""
        std = pd.Series(values).rolling(len(sma)).std()
        return sma + std_dev * std
    
    @staticmethod
    def lower_band(values, sma, std_dev):
        """计算布林带下轨"""
        std = pd.Series(values).rolling(len(sma)).std()
        return sma - std_dev * std
