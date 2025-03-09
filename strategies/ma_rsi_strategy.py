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
        self.fast_ma_line = self.I(self.SMA, price, self.fast_ma)
        self.slow_ma_line = self.I(self.SMA, price, self.slow_ma)
        
        # 计算RSI指标
        self.rsi = self.I(self.RSI, price, self.rsi_period)
        
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
    
    @staticmethod
    def SMA(values, n):
        """计算简单移动平均线"""
        return pd.Series(values).rolling(n).mean()
    
    @staticmethod
    def RSI(values, n):
        """
        计算相对强弱指数 (RSI)
        
        参数:
        - values: 价格序列
        - n: 周期
        
        返回:
        - RSI值序列 (0-100)
        """
        # 转换为pandas Series
        close = pd.Series(values)
        
        # 计算价格变化
        delta = close.diff()
        
        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均上涨和下跌
        avg_gain = gain.rolling(window=n).mean()
        avg_loss = loss.rolling(window=n).mean()
        
        # 计算相对强度 (RS)
        rs = avg_gain / avg_loss
        
        # 计算RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
