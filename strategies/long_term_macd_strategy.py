#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
长期MACD交易策略
基于月线、周线MACD指标和日线EMA的多周期策略
"""

import pandas as pd
import numpy as np
from backtesting import Strategy
from common.timeframe_utils import (
    resample_to_weekly,
    resample_to_monthly,
    map_higher_timeframe_to_daily
)
from common.indicators import MACD, EMA, SMA, KDJ


class LongTermMACDStrategy(Strategy):
    """
    长期MACD策略
    
    使用月线、周线和日线的MACD指标进行多周期共振分析，寻找长期趋势的买卖点。
    
    买入条件:
    1. 月线KDJ金叉
    2. 月线MACD DIF斜率向上
    3. 周线MACD金叉
    
    卖出条件:
    1. 月线MACD值下降
    2. 周线MACD死叉且MACD值<0
    
    策略特点:
    - 适合长期投资者
    - 捕捉大级别趋势行情
    - 减少交易频率，降低交易成本
    """
    
    # 定义策略参数
    # MACD
    fast_period = 12
    slow_period = 26
    signal_period = 9
    
    # KDJ
    kdj_k_period = 9
    kdj_d_period = 3
    kdj_j_period = 3
    
    # EMA
    ema_period = 20
    
    price_range_pct = 0.05  # 筹码集中区域上下浮动5%
    stop_loss_pct = 0.05
    take_profit_pct = 0.1
    
    # 仓位管理参数
    position_size = 0.9      # 默认仓位大小（1.0表示全仓）
    downtrend_exit_size = 0.5  # 趋势反转时卖出的仓位比例
    
    # 上升下降大趋势
    in_uptrend = False
    in_downtrend = False

    
    def init(self):
        """初始化策略，计算指标"""
        # 使用当前数据计算指标（如果是月线，则直接使用）
        # 添加多个周期的EMA均线
        # self.ema5 = self.I(EMA, self.data.Close, 5, overlay=True, name='EMA5', color='#FF5733')
        # self.ema10 = self.I(EMA, self.data.Close, 10, overlay=True, name='EMA10', color='#33FF57')
        self.ema20 = self.I(EMA, self.data.Close, 20, overlay=True, name='EMA20', color='#3357FF')
        # self.ema60 = self.I(EMA, self.data.Close, 60, overlay=True, name='EMA60', color='#FF33A8')
        # self.ema120 = self.I(EMA, self.data.Close, 120, overlay=True, name='EMA120', color='#33FFF6')
        # self.ema250 = self.I(EMA, self.data.Close, 250, overlay=True, name='EMA250', color='#F6FF33')
        
        # 计算MACD指标，设置overlay=False使其显示在单独的图表中
        self.dif, self.dea, self.macd = self.I(MACD, 
            self.data.Close, self.fast_period, self.slow_period, self.signal_period,
            overlay=False
        )
        
        # 计算KDJ指标，设置overlay=False使其显示在单独的图表中
        self.k, self.d, self.j = self.I(KDJ, 
            self.data.High, self.data.Low, self.data.Close, 
            self.kdj_k_period, self.kdj_d_period, self.kdj_j_period,
            overlay=False
        )
        
        # 初始化状态变量
        self.monthly_kdj_golden_cross_active = False
        self.weekly_kdj_golden_cross_active = False
        
        # 不显示价格中枢
        # self.price_center = self.I(EMA, self.data.Close, 120, overlay=True)
        
        # 初始化交易状态
        self.stop_loss_price = 0
        self.take_profit_price = 0
        self.in_uptrend = False       # 上涨大趋势
        self.in_downtrend = False     # 下跌大趋势
        
        # 记录上一次计算大趋势的月份
        self.last_trend_check_month = None
        
        # 获取周线和月线数据
        self.weekly_data = resample_to_weekly(self.data.df.copy())
        self.monthly_data = resample_to_monthly(self.data.df.copy())
        
        # 计算日线指标
        # 使用已经计算的EMA20作为daily_ema
        self.daily_ema = self.ema20
        self.daily_dif, self.daily_dea, self.daily_macd = self.I(MACD, 
            self.data.Close, self.fast_period, self.slow_period, self.signal_period
        )
        
        # 计算周线指标
        weekly_close = self.weekly_data['Close']
        weekly_high = self.weekly_data['High']
        weekly_low = self.weekly_data['Low']
        self.weekly_dif, self.weekly_dea, self.weekly_macd = MACD(
            weekly_close, self.fast_period, self.slow_period, self.signal_period
        )
        self.weekly_k, self.weekly_d, self.weekly_j = KDJ(
            weekly_high, weekly_low, weekly_close, 
            self.kdj_k_period, self.kdj_d_period, self.kdj_j_period
        )
        
        # 计算月线指标
        monthly_close = self.monthly_data['Close']
        self.monthly_dif, self.monthly_dea, self.monthly_macd = MACD(
            monthly_close, self.fast_period, self.slow_period, self.signal_period
        )
        
        # 计算月线KDJ指标
        monthly_high = self.monthly_data['High']
        monthly_low = self.monthly_data['Low']
        self.monthly_k, self.monthly_d, self.monthly_j = KDJ(
            monthly_high, monthly_low, monthly_close, 
            self.kdj_k_period, self.kdj_d_period, self.kdj_j_period
        )
        
        # 将月线KDJ指标映射到日线时间框架，用于绘图
        # 创建一个函数来映射月线数据到日线
        def map_monthly_to_daily(monthly_series, name=None):
            # 创建一个与日线数据索引相同的空Series
            daily_index = self.data.index
            result = pd.Series(index=daily_index, dtype=float)
            
            # 对于每个日期，找到对应的月线数据
            for date in daily_index:
                # 找到日期之前的最后一个月线数据点
                mask = monthly_series.index <= date
                if mask.any():
                    last_value = monthly_series[mask].iloc[-1]
                    result[date] = last_value
            
            # 前向填充缺失值
            result = result.ffill()
            return result
        
        # 映射月线KDJ指标到日线
        monthly_k_daily = map_monthly_to_daily(self.monthly_k)
        monthly_d_daily = map_monthly_to_daily(self.monthly_d)
        monthly_j_daily = map_monthly_to_daily(self.monthly_j)
        
        # 将月线MACD指标映射到日线时间框架，用于绘图
        monthly_dif_daily = map_monthly_to_daily(self.monthly_dif)
        monthly_dea_daily = map_monthly_to_daily(self.monthly_dea)
        monthly_macd_daily = map_monthly_to_daily(self.monthly_macd)
        
       
        # 计算月线EMA20均线
        self.monthly_ema20 = EMA(monthly_close, self.ema_period)
        
        # 计算月线MACD的DIF斜率（用于判断是否向上）
        self.monthly_dif_slope = self.monthly_dif.diff()
        
        # 计算筹码集中区域（使用简单的20日均价作为筹码集中区域的中心）
        # self.price_center = self.I(SMA, self.data.Close, 20)
        
        # 添加状态变量，用于跟踪大趋势
        self.in_uptrend = False       # 上涨大趋势
        self.in_downtrend = False     # 下跌大趋势
        
        # 记录上一次计算大趋势的月份
        self.last_trend_check_month = None
        
    def next(self):
        """策略主逻辑"""
        # 获取当前价格和日期
        price = self.data.Close[-1]  
        current_date = self.data.index[-1]
        
        # ===== 月线信号判断 =====
        # 检查月线KDJ金叉和死叉
        current_kd_diff = self.k[-1] - self.d[-1]  
        prev_kd_diff = self.k[-2] - self.d[-2]
        
        # 获取当前月份和上个月份的数据，用于计算月线DIF斜率
        current_month = current_date.month
        current_year = current_date.year
        
        # 查找当前月份的月线数据
        monthly_index = self.monthly_data.index
        current_month_data = self.monthly_data[
            (monthly_index.month == current_month) & 
            (monthly_index.year == current_year)
        ]
        
        # 查找上个月的月线数据
        prev_month = current_month - 1 if current_month > 1 else 12
        prev_year = current_year if current_month > 1 else current_year - 1
        prev_month_data = self.monthly_data[
            (monthly_index.month == prev_month) & 
            (monthly_index.year == prev_year)
        ]
        
        # 如果找到了当前月和上个月的数据，计算DIF斜率
        if not current_month_data.empty and not prev_month_data.empty:
            current_monthly_dif = self.monthly_dif[current_month_data.index[0]]
            prev_monthly_dif = self.monthly_dif[prev_month_data.index[0]]
            current_monthly_macd = self.monthly_macd[current_month_data.index[0]]
            
            # 计算DIF斜率
            monthly_dif_slope = current_monthly_dif - prev_monthly_dif
            
            # print(f"当前月线DIF: {current_monthly_dif:.4f}, 上一月DIF: {prev_monthly_dif:.4f}, DIF斜率: {monthly_dif_slope:.4f}")
        else:
            # 如果找不到数据，使用默认值
            current_monthly_dif = self.monthly_dif[-1]
            prev_monthly_dif = self.monthly_dif[-2] if len(self.monthly_dif) > 1 else 0
            current_monthly_macd = self.monthly_macd[-1]
            monthly_dif_slope = current_monthly_dif - prev_monthly_dif
            
        # 判断月线KDJ金叉：K线上穿D线
        if current_kd_diff > 0 and prev_kd_diff <= 0:
            # 月线KDJ金叉
            self.monthly_kdj_golden_cross_active = True
        # 判断月线KDJ死叉：K线下穿D线
        elif current_kd_diff < 0 and prev_kd_diff >= 0:
            # 月线KDJ死叉
            self.monthly_kdj_golden_cross_active = False
        
        # 判断大趋势
        # 1. 首先检查月线KDJ金叉状态
        if self.monthly_kdj_golden_cross_active:
            # 2. 再检查月线MACD值>0且DIF线斜率向上
            monthly_macd_positive = current_monthly_macd > 0
            monthly_dif_rising = monthly_dif_slope > 0  # 使用新计算的斜率
            
            # 只有当月线MACD>0且DIF值斜率向上时，才继续判断周线
            if monthly_macd_positive and monthly_dif_rising:
                
                # 已经检查过月线条件，这里直接判断上涨大趋势
                if not self.in_uptrend:
                    self.in_uptrend = True
                    self.in_downtrend = False
                    print(f"月线周线共振：进入上涨大趋势: {current_date.strftime('%Y-%m-%d')}")
        else:

            # 2. 再检查月线MACD DIF线斜率向下
            monthly_dif_rising = monthly_dif_slope < 0  # 使用新计算的斜率
            
            # 只有当月线MACD<0且DIF值斜率向下时，才继续判断周线
            if monthly_dif_rising:
                # 月线KDJ死叉，可能是下跌大趋势
                if not self.in_downtrend:
                    self.in_downtrend = True
                    self.in_uptrend = False
                print(f"下跌大趋势: {self.data.index[-1].strftime('%Y-%m-%d')}")
        
        # ===== 交易逻辑 =====·
        if not self.position:  # 没有持仓
            # 只在上涨大趋势中开仓
            if self.in_uptrend:
                # 计算止损和止盈价格
                self.stop_loss_price = price * (1 - self.stop_loss_pct)
                self.take_profit_price = price * (1 + self.take_profit_pct)
                
                # 开仓买入
                self.buy(size=self.position_size)
                print(f"买入: {self.data.index[-1].strftime('%Y-%m-%d')} 价格: {price:.2f}")
        
        else:  # 有持仓
            # 检查止损和止盈
            if price <= self.stop_loss_price:
                # 触发止损
                self.position.close()
                print(f"止损卖出: {self.data.index[-1].strftime('%Y-%m-%d')} 价格: {price:.2f}")
            elif price >= self.take_profit_price:
                # 触发止盈
                self.position.close()
                print(f"止盈卖出: {self.data.index[-1].strftime('%Y-%m-%d')} 价格: {price:.2f}")
            # 大趋势反转也卖出
            elif self.in_downtrend:
                # 部分卖出
                self.position.close(self.downtrend_exit_size)
                print(f"趋势反转卖出{self.downtrend_exit_size*100}%: {self.data.index[-1].strftime('%Y-%m-%d')} 价格: {price:.2f}")
