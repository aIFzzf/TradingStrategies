#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
双均线交易策略
当短期均线上穿长期均线时买入，当短期均线下穿长期均线时卖出
"""

import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover


class DualMAStrategy(Strategy):
    """
    双均线交易策略
    
    参数:
    - fast_ma: 短期均线周期
    - slow_ma: 长期均线周期
    - stop_loss_pct: 止损百分比 (0.05 表示 5%)
    - take_profit_pct: 止盈百分比 (0.1 表示 10%)
    """
    # 定义策略参数，可以在回测时进行优化
    fast_ma = 10
    slow_ma = 30
    stop_loss_pct = 0.05
    take_profit_pct = 0.1
    
    def init(self):
        """初始化策略，计算指标"""
        # 获取收盘价
        price = self.data.Close
        
        # 计算快速和慢速移动平均线
        self.fast_ma_line = self.I(self.SMA, price, self.fast_ma)
        self.slow_ma_line = self.I(self.SMA, price, self.slow_ma)
    
    def next(self):
        """
        每个新的K线数据到来时执行的逻辑
        决定是否买入或卖出
        """
        price = self.data.Close[-1]  # 当前收盘价
        
        # 如果没有持仓，检查买入信号
        if not self.position:
            # 当短期均线上穿长期均线时买入
            if crossover(self.fast_ma_line, self.slow_ma_line):
                # 计算止损和止盈价格
                stop_loss = price * (1 - self.stop_loss_pct)
                take_profit = price * (1 + self.take_profit_pct)
                
                # 买入，并设置止损和止盈
                self.buy(sl=stop_loss, tp=take_profit)
        
        # 如果有持仓，检查卖出信号
        else:
            # 当短期均线下穿长期均线时卖出
            if crossover(self.slow_ma_line, self.fast_ma_line):
                self.position.close()
    
    @staticmethod
    def SMA(values, n):
        """
        计算简单移动平均线
        
        参数:
        - values: 价格序列
        - n: 周期
        
        返回:
        - 移动平均线序列
        """
        return pd.Series(values).rolling(n).mean()
