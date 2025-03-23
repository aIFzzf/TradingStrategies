#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日线MACD期权策略

该策略基于日线MACD指标，用于期权交易。
买入条件：日线MACD金叉且未死叉
卖出条件：日线MACD死叉
"""

import pandas as pd
import numpy as np
from datetime import datetime

# 导入指标计算函数
from common.indicators import MACD, EMA

class DailyMACDOptionStrategy:
    """
    日线MACD期权策略
    
    该策略基于日线MACD指标，用于期权交易。
    买入条件：日线MACD金叉且未死叉
    卖出条件：日线MACD死叉
    """
    
    # MACD参数
    fast_period = 12
    slow_period = 26
    signal_period = 9
    
    def __init__(self, data):
        """
        初始化策略
        
        参数：
        - data：DataFrame，股票数据
        """
        self.data = data
        self.position = None
        
        # 计算日线MACD指标
        self.daily_dif, self.daily_dea, self.daily_macd = MACD(
            self.data['Close'], 
            self.fast_period, 
            self.slow_period, 
            self.signal_period
        )
        
        # 记录MACD金叉和死叉状态
        self.macd_golden_cross_active = False
        
        # 记录信号
        self.signals = []
    
    def next(self):
        """策略主逻辑"""
        # 获取当前价格和日期
        price = self.data['Close'].iloc[-1]
        date = self.data.index[-1]
        
        # 获取当前和前一天的MACD值
        current_dif = self.daily_dif.iloc[-1]
        current_dea = self.daily_dea.iloc[-1]
        
        if len(self.daily_dif) > 1 and len(self.daily_dea) > 1:
            prev_dif = self.daily_dif.iloc[-2]
            prev_dea = self.daily_dea.iloc[-2]
            
            # 判断MACD金叉：DIF上穿DEA
            macd_golden_cross = current_dif > current_dea and prev_dif <= prev_dea
            
            # 判断MACD死叉：DIF下穿DEA
            macd_death_cross = current_dif < current_dea and prev_dif >= prev_dea
            
            # 更新MACD金叉状态
            if macd_golden_cross:
                self.macd_golden_cross_active = True
                # 记录买入信号
                self.signals.append({
                    'date': date,
                    'price': price,
                    'action': 'buy',
                    'reason': '日线MACD金叉'
                })
                
                # 执行买入操作
                if self.position is None:
                    self.position = {'open_price': price, 'size': 1.0}
                    print(f"买入信号: {date.strftime('%Y-%m-%d')} 价格: {price:.2f} 原因: 日线MACD金叉")
            
            # 如果出现MACD死叉，则退出多头
            if macd_death_cross and self.macd_golden_cross_active:
                self.macd_golden_cross_active = False
                # 记录卖出信号
                self.signals.append({
                    'date': date,
                    'price': price,
                    'action': 'sell',
                    'reason': '日线MACD死叉'
                })
                
                # 执行卖出操作
                if self.position is not None:
                    print(f"卖出信号: {date.strftime('%Y-%m-%d')} 价格: {price:.2f} 原因: 日线MACD死叉")
                    self.position = None
    
    @staticmethod
    def is_in_uptrend(data, lookback_days=30):
        """
        判断最近指定天数内是否有MACD金叉
        
        参数：
        - data：DataFrame，股票数据
        - lookback_days：int，往前查找的天数，默认30天
        
        返回：
        - bool：是否在最近指定天数内有MACD金叉
        """
        # 计算日线MACD指标
        daily_dif, daily_dea, daily_macd = MACD(
            data['Close'], 
            DailyMACDOptionStrategy.fast_period, 
            DailyMACDOptionStrategy.slow_period, 
            DailyMACDOptionStrategy.signal_period
        )
        
        # 获取最近的数据
        if len(daily_dif) <= lookback_days:
            recent_data_length = len(daily_dif)
        else:
            recent_data_length = lookback_days
        
        recent_dif = daily_dif[-recent_data_length:]
        recent_dea = daily_dea[-recent_data_length:]
        
        # 判断最近指定天数内是否有MACD金叉
        has_golden_cross = False
        
        for i in range(1, len(recent_dif)):
            current_dif = recent_dif.iloc[i]
            current_dea = recent_dea.iloc[i]
            prev_dif = recent_dif.iloc[i-1]
            prev_dea = recent_dea.iloc[i-1]
            
            # 判断MACD金叉：DIF上穿DEA
            if current_dif > current_dea and prev_dif <= prev_dea:
                has_golden_cross = True
                break
        
        # 检查当前是否处于MACD多头排列（DIF > DEA）
        is_bullish_alignment = False
        if len(recent_dif) > 0 and len(recent_dea) > 0:
            is_bullish_alignment = recent_dif.iloc[-1] > recent_dea.iloc[-1]
        
        # 同时满足两个条件：最近有金叉且当前是多头排列
        return has_golden_cross and is_bullish_alignment
    
    @staticmethod
    def calculate_trend_indicators(data, lookback_days=30):
        """
        计算各种技术指标并判断趋势，供外部调用
        
        参数：
        - data：DataFrame，股票数据
        - lookback_days：int，往前查找的天数，默认30天
        
        返回：
        - dict：包含各种技术指标和趋势判断的字典
        """
        # 计算日线MACD指标
        daily_dif, daily_dea, daily_macd = MACD(
            data['Close'], 
            DailyMACDOptionStrategy.fast_period, 
            DailyMACDOptionStrategy.slow_period, 
            DailyMACDOptionStrategy.signal_period
        )
        
        # 判断是否处于上升趋势中
        in_uptrend = pd.Series(False, index=data.index)
        
        # 对每一天，检查之前的lookback_days天内是否有金叉
        for i in range(lookback_days, len(data)):
            # 获取当前日期
            current_date = data.index[i]
            
            # 获取最近lookback_days天的数据
            start_idx = max(0, i - lookback_days)
            recent_dif = daily_dif.iloc[start_idx:i+1]
            recent_dea = daily_dea.iloc[start_idx:i+1]
            
            # 判断是否有金叉
            has_golden_cross = False
            for j in range(1, len(recent_dif)):
                current_dif_value = recent_dif.iloc[j]
                current_dea_value = recent_dea.iloc[j]
                prev_dif_value = recent_dif.iloc[j-1]
                prev_dea_value = recent_dea.iloc[j-1]
                
                # 判断MACD金叉：DIF上穿DEA
                if current_dif_value > current_dea_value and prev_dif_value <= prev_dea_value:
                    has_golden_cross = True
                    break
            
            # 检查当前是否处于MACD多头排列（DIF > DEA）
            is_bullish_alignment = daily_dif.iloc[i] > daily_dea.iloc[i]
            
            # 同时满足两个条件：最近有金叉且当前是多头排列
            in_uptrend[current_date] = has_golden_cross and is_bullish_alignment
        
        # 返回所有指标
        return {
            'daily': {
                'dif': daily_dif,
                'dea': daily_dea,
                'macd': daily_macd
            },
            'trend': {
                'in_uptrend': in_uptrend,
                'in_downtrend': ~in_uptrend  # 非上升趋势即为下降趋势
            }
        }
    
    @staticmethod
    def judge_signals(data, indicators=None, lookback_days=30):
        """
        判断买入卖出信号，供外部调用
        
        参数：
        - data：DataFrame，股票数据
        - indicators：dict，可选，已计算好的指标，如果为None则会自动计算
        - lookback_days：int，往前查找的天数，默认30天
        
        返回：
        - dict：包含买入卖出信号的字典
        """
        # 如果没有提供指标，则计算指标
        if indicators is None:
            indicators = DailyMACDOptionStrategy.calculate_trend_indicators(data, lookback_days)
        
        # 获取最新日期的数据
        latest_date = data.index[-1]
        
        # 获取各项指标的最新值
        in_uptrend = indicators['trend']['in_uptrend'][-1]
        
        # 判断买入信号
        buy_signal = in_uptrend
        
        # 判断卖出信号
        sell_signal = not in_uptrend
        
        # 返回判断结果
        return {
            'buy_signal': buy_signal,
            'sell_signal': sell_signal,
            'in_uptrend': in_uptrend,
            'in_downtrend': not in_uptrend,
            'date': latest_date
        }
