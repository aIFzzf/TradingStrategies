#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
长期MACD交易策略
基于月线MACD、周线KDJ和日线EMA的多周期策略
使用月线MACD判断大趋势方向，配合周线KDJ和日线EMA确认交易信号
"""

from matplotlib.pyplot import plot
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import resample_apply, crossover

from common.timeframe_utils import (
    resample_to_weekly,
    resample_to_monthly,
    map_higher_timeframe_to_daily
)
from common.indicators import MACD, EMA, SMA, KDJ

import logging
import os
from datetime import datetime

# 设置日志记录器
def setup_logger(symbol):
    # 创建logs目录（如果不存在）
    os.makedirs('logs', exist_ok=True)
    
    # 生成日志文件名（包含股票代码和当前日期时间）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/macd_strategy_{symbol}_{timestamp}.log'
    
    # 配置日志记录器
    logger = logging.getLogger(f'macd_strategy_{symbol}')
    logger.setLevel(logging.INFO)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到日志记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class LongTermMACDStrategy(Strategy):
    """
    长期MACD策略
    
    使用月线MACD判断大趋势方向，配合周线KDJ和日线EMA确认交易信号，
    能够有效降低交易频率，减少交易成本和心理压力。
    
    策略评分系统:
    - 月线MACD > 0.1: +10分，否则-10分
    - 周线KDJ金叉: +20分，否则-20分
    - 日线EMA上穿: +10分，否则-10分
    - 总分超过20分时产生买入信号
    - 总分低于0分时产生卖出信号
    
    策略特点:
    - 适合长期投资者
    - 捉捉大级别趋势行情
    - 减少交易频率，降低交易成本
    - 使用多周期确认，提高信号可靠性
    """
    
    # MACD参数 - 策略类参数必须定义为类变量
    fast_period = 12
    slow_period = 26
    signal_period = 9
    
    # KDJ参数
    kdj_k_period = 9
    kdj_d_period = 3
    kdj_j_period = 3
    
    # EMA参数
    ema_period = 20
    
    # 价格参数
    price_range_pct = 0.05
    stop_loss_pct = 0.2
    take_profit_pct = 0.9
    
    # 仓位参数
    position_size = 1.0
    downtrend_exit_size = 0.5
    
    # 上升下降大趋势
    in_uptrend = False
    in_downtrend = False

    buy_signal = False
    sell_signal = False


    # 买入卖出得分阈值
    buy_threshold = 20      # 买入阈值
    sell_threshold = 0      # 卖出阈值
    
    # 得分权重
    monthly_macd_positive_weight = 10   # 月线MACD值>0的得分权重
    weekly_kdj_cross_weight = 20        # 周线KDJ金叉的得分权重
    daily_ema_cross_weight = 10          # 日线EMA上穿月线EMA的得分权重

    def init(self):
        """
        初始化策略，计算各周期指标
        
        包括初始化日志记录器、重采样数据到周线和月线、
        计算日线EMA、周线KDJ和月线MACD指标
        """
        # 初始化日志记录器
        # 获取股票符号作为日志文件名的一部分
        try:
            if hasattr(self.data, 'df') and len(self.data.df) > 0:
                if hasattr(self.data.df['Close'], 'name'):
                    self.symbol = self.data.df['Close'].name 
                else:
                    self.symbol = 'unknown'
            else:
                self.symbol = 'unknown'
                
            # 初始化日志记录器
            self.logger = setup_logger(self.symbol)
            self.logger.info(f"初始化长期MACD策略，股票代码: {self.symbol}")
            # self.logger.info(f"MACD参数: fast={self.fast_period}, slow={self.slow_period}, signal={self.signal_period}")
            # self.logger.info(f"KDJ参数: K={self.kdj_k_period}, D={self.kdj_d_period}, J={self.kdj_j_period}")
        except Exception as e:
            # 如果日志记录器初始化失败，不要中断策略的执行
            print(f"日志记录器初始化失败: {e}")
        
        # 使用当前数据计算指标
        # self.ema20 = self.I(EMA, self.data.Close, 20, overlay=True, name='EMA20', color='#3357FF')
       
        
        # 计算MACD指标，使其显示在自己的副图中
        self.dif, self.dea, self.macd = self.I(MACD, 
            self.data.Close, self.fast_period, self.slow_period, self.signal_period,
            overlay=False
        )
        
        # 计算KDJ指标，使其显示在自己的副图中
        self.k, self.d, self.j = self.I(KDJ, 
            self.data.High, self.data.Low, self.data.Close, 
            self.kdj_k_period, self.kdj_d_period, self.kdj_j_period,
            overlay=False
        )
        
        # 初始化状态变量
        self.monthly_kdj_golden_cross_active = False
        self.weekly_kdj_golden_cross_active = False
        
        # 初始化MACD金叉死叉状态
        self.weekly_macd_golden_cross = False
        self.weekly_macd_death_cross = False
        self.monthly_macd_golden_cross = False
        self.monthly_macd_death_cross = False
        
        # 初始化KDJ金叉死叉状态
        self.weekly_kdj_golden_cross = False
        self.weekly_kdj_death_cross = False
        self.monthly_kdj_golden_cross = False
        self.monthly_kdj_death_cross = False
        
        # 不显示价格中枢
        # self.price_center = self.I(EMA, self.data.Close, 120, overlay=True)


        # 初始化交易状态
        self.stop_loss_price = 0
        self.take_profit_price = 0
        self.in_uptrend = False       # 上涨大趋势
        self.in_downtrend = False     # 下跌大趋势
        
        # 初始化得分系统
        self.total_score = 0           # 总得分
        self.score_history = []        # 得分历史记录
        
        # 记录上一次计算大趋势的月份
        self.last_trend_check_month = None
        
        # 获取周线和月线数据 - 每个交易日使用最新数据计算
        self.daily_data = self.data.df
        
        # 初始化数据框架 - 这里仅供初始化，在next方法中会动态更新
        self.weekly_data = resample_to_weekly(self.daily_data.copy())
        self.monthly_data = resample_to_monthly(self.daily_data.copy()) 
        
        # 打印重采样数据信息，用于调试
        print(f"数据重采样结果 - 日线数据: {len(self.daily_data)}条, 周线数据: {len(self.weekly_data)}条, 月线数据: {len(self.monthly_data)}条")
        
        
        
        # 日线指标计算 
        self.daily_ema = self.I(EMA, self.data.Close, self.ema_period, overlay=True, name='EMA20', color='#3357FF')
        self.dif, self.dea, self.macd = self.I(MACD, 
            self.data.Close, self.fast_period, self.slow_period, self.signal_period,
            overlay=False
        )
        self.k, self.d, self.j = self.I(KDJ, 
            self.data.High, self.data.Low, self.data.Close, 
            self.kdj_k_period, self.kdj_d_period, self.kdj_j_period,
            overlay=False
        )
        
        # 周线和月线指标将在next方法中动态计算
        # 这里只是初始化相关变量
        self.weekly_dif = None
        self.weekly_dea = None
        self.weekly_macd = None
        self.weekly_k = None
        self.weekly_d = None
        self.weekly_j = None
        
        self.monthly_dif = None
        self.monthly_dea = None
        self.monthly_macd = None
        self.monthly_k = None
        self.monthly_d = None
        self.monthly_j = None
        
        # 存储上一个交易日的数据日期，用于判断是否需要更新周线和月线数据
        self.last_date = None
        
            
        # 添加状态变量，用于跟踪大趋势
        self.in_uptrend = False       # 上涨大趋势
        self.in_downtrend = False     # 下跌大趋势
        
        # 记录上一次计算大趋势的月份
        self.last_trend_check_month = None



    


    def next(self):
        """
        处理每个交易日的数据
        
        主要流程:
        1. 更新周线和月线数据
        2. 计算各周期指标
        3. 基于指标计算得分
        4. 根据月线MACD判断大趋势
        5. 根据总得分和大趋势执行交易决策
        """
        price = self.data.Close[-1]  # 当前收盘价
        current_date = self.data.index[-1]  # 当前日期
        
        # 获取当前日期所在的周和月
        current_week = current_date.strftime('%Y-%W')  # 年-周
        current_month = current_date.strftime('%Y-%m')  # 年-月
        
        # 首次运行时初始化数据
        if self.last_date is None:
            # 初始化数据
            current_data = self.data.df.loc[:current_date].copy()
            self.weekly_data = resample_to_weekly(current_data)
            self.monthly_data = resample_to_monthly(current_data)
            # print(f"[初始化数据] 当前日期: {current_date.date()}, 周: {current_week}, 月: {current_month}")
        # 如果日期前进了，检查是否需要更新周线和月线数据
        elif current_date > self.last_date:
            # 获取上一个交易日的周和月
            last_week = self.last_date.strftime('%Y-%W')
            last_month = self.last_date.strftime('%Y-%m')
            
            # 当前日线数据
            current_data = self.data.df.loc[:current_date].copy()
            
            # 只在周变化时更新周线数据
            if current_week != last_week:
                self.weekly_data = resample_to_weekly(current_data)
                # print(f"[更新周线数据] 当前日期: {current_date.date()}, 当前周: {current_week}, 前一周: {last_week}")
            # 只在月变化时更新月线数据
            if current_month != last_month:
                self.monthly_data = resample_to_monthly(current_data)
                # print(f"[更新月线数据] 当前日期: {current_date.date()}, 当前月: {current_month}, 前一月: {last_month}")
        
            
          
            # 计算周线指标
            if len(self.weekly_data) > self.slow_period + self.signal_period:
                weekly_close = self.weekly_data['Close']
                weekly_high = self.weekly_data['High']
                weekly_low = self.weekly_data['Low']
                
                # 计算周线MACD指标
                self.weekly_dif, self.weekly_dea, self.weekly_macd = MACD(
                    weekly_close, self.fast_period, self.slow_period, self.signal_period
                )
                
                # 检测周线MACD金叉和死叉
                # 判断是否DIF上穿DEA
                dif_crossed_over = crossover(self.weekly_dif, self.weekly_dea)  # DIF上穿DEA
                
                # 同时检查DIF与DEA的差值是否大于0.15，满足两个条件才算真正的金叉信号
                if dif_crossed_over and len(self.weekly_dif) > 0 and len(self.weekly_dea) > 0:
                    # 计算最新的DIF和DEA的差值
                    diff_value = self.weekly_dif.iloc[-1] - self.weekly_dea.iloc[-1]
                    # 只有差值大于0.15才认为是有效的金叉信号
                    self.weekly_macd_golden_cross = diff_value > 0.09
                else:
                    self.weekly_macd_golden_cross = False
                    

                if  self.weekly_macd_golden_cross:
                    self.weekly_macd_death_cross = False
                else:
                    self.weekly_macd_death_cross = True
                
                # 计算周线KDJ指标
                self.weekly_k, self.weekly_d, self.weekly_j = KDJ(
                    weekly_high, weekly_low, weekly_close, 
                    self.kdj_k_period, self.kdj_d_period, self.kdj_j_period
                )
                
                
                # 只在当周的最后一个交易日计算KDJ指标
                if len(self.weekly_k) > 0 and len(self.weekly_d) > 0:
                    current_k = self.weekly_k.iloc[-1]
                    current_d = self.weekly_d.iloc[-1]
                    kd_diff = current_k - current_d
                    current_date_str = current_date.strftime('%Y-%m-%d')
                    
                    # 使用日志记录器记录KDJ数据
                    # if hasattr(self, 'logger'):
                    #     self.logger.info(f"[周线KDJ] 日期: {current_date_str}, K: {current_k:.2f}, D: {current_d:.2f}, 差值: {kd_diff:.2f}")
                    
                    # 简化判断，K-D>0为看涨信号，K-D<0为看跌信号
                    self.weekly_kdj_golden_cross = kd_diff > 0  # K值大于D值为看涨信号
                    self.weekly_kdj_death_cross = kd_diff < 0   # K值小于D值为看跌信号
                    
                    # 在日志中记录信号
                    # if self.weekly_kdj_golden_cross and hasattr(self, 'logger'):
                    #     self.logger.info(f"周线KDJ看涨信号! K-D差值: {kd_diff:.2f} > 0, 日期: {current_date_str}")
                    # elif self.weekly_kdj_death_cross and hasattr(self, 'logger'):
                    #     self.logger.info(f"周线KDJ看跌信号! K-D差值: {kd_diff:.2f} < 0, 日期: {current_date_str}")
                    
                else:
                    self.weekly_kdj_golden_cross = False
                    self.weekly_kdj_death_cross = False
                
            
            # 计算月线指标
            if len(self.monthly_data) > self.slow_period + self.signal_period:
                monthly_close = self.monthly_data['Close']
                monthly_high = self.monthly_data['High']
                monthly_low = self.monthly_data['Low']
                
                # 计算月线MACD指标
                self.monthly_dif, self.monthly_dea, self.monthly_macd = MACD(
                    monthly_close, self.fast_period, self.slow_period, self.signal_period
                )
                
                # 检测月线MACD金叉和死叉
                self.monthly_macd_golden_cross = crossover(self.monthly_dif, self.monthly_dea)  # DIF上穿DEA - 金叉
                self.monthly_macd_death_cross = crossover(self.monthly_dea, self.monthly_dif)   # DEA上穿DIF - 死叉
                
                # 计算月线KDJ指标
                self.monthly_k, self.monthly_d, self.monthly_j = KDJ(
                    monthly_high, monthly_low, monthly_close, 
                    self.kdj_k_period, self.kdj_d_period, self.kdj_j_period
                )
                
                # 检测月线KDJ金叉和死叉
                self.monthly_kdj_golden_cross = crossover(self.monthly_k, self.monthly_d)  # K上穿D - 金叉
                self.monthly_kdj_death_cross = crossover(self.monthly_d, self.monthly_k)   # D上穿K - 死叉
                
                # 计算月线EMA20均线
                self.monthly_ema20 = EMA(monthly_close, self.ema_period)
            
        # 更新最后处理的日期
        self.last_date = current_date
        
        # 利用得分系统评估当前市场状况
        # 首先重置总得分
        self.total_score = 0
        
        # 1. 检查月线MACD值是否>0.1
        if hasattr(self, 'monthly_macd') and self.monthly_macd is not None and len(self.monthly_macd) > 0.1:
            current_monthly_macd = self.monthly_macd.iloc[-1]
            monthly_macd_positive = current_monthly_macd > 0.1
          
            # 如果月线MACD值大于0，加上对应权重的分数
            if monthly_macd_positive:
                self.total_score += self.monthly_macd_positive_weight
                # if hasattr(self, 'logger'):
                #     self.logger.info(f"当前日期: {current_date.strftime('%Y-%m-%d')}, 月线MACD值大于0.1: +{self.monthly_macd_positive_weight}分，总分：{self.total_score}")
            else:
                self.total_score -= self.monthly_macd_positive_weight
               
        
        # 2. 检查月线MACD DIF线斜率向上
        # monthly_dif_rising = monthly_dif_slope > 0
        # if monthly_dif_rising:
        #     self.total_score += self.monthly_dif_rising_weight
            # print(f"月线MACD DIF斜率向上: +{self.monthly_dif_rising_weight}分")
        # else:
        #     print("月线MACD DIF斜率向下: +0分")
            
        # 3. 检查周线KDJ金叉状态
        if hasattr(self, 'weekly_kdj_golden_cross') and self.weekly_kdj_golden_cross:
            self.total_score += self.weekly_kdj_cross_weight
            # if hasattr(self, 'logger'):
            #     self.logger.info(f"当前日期: {current_date.strftime('%Y-%m-%d')},周线KDJ金叉: +{self.weekly_kdj_cross_weight}分，总分：{self.total_score}")
        else:
            self.total_score -= self.weekly_kdj_cross_weight
            # 可选的负分日志
            # if hasattr(self, 'logger'):
                # self.logger.info(f"当前日期: {current_date.strftime('%Y-%m-%d')},周线KDJ无金叉: -{self.weekly_kdj_cross_weight}分")
            
        # 4. 检查周线MACD金叉
        # if hasattr(self, 'weekly_macd_golden_cross') and self.weekly_macd_golden_cross:
        #     # self.total_score += self.weekly_macd_cross_weight
        #     # print(f"周线MACD金叉: +{self.weekly_macd_cross_weight}分")
            
        #     # 如果需要显示更多详细信息，可以打印当前周的DIF和DEA值
        #     if hasattr(self, 'weekly_dif') and hasattr(self, 'weekly_dea') and \
        #        self.weekly_dif is not None and self.weekly_dea is not None and \
        #        len(self.weekly_dif) > 0 and len(self.weekly_dea) > 0:
        #         current_weekly_dif = self.weekly_dif.iloc[-1]
        #         current_weekly_dea = self.weekly_dea.iloc[-1]
        #         current_diff = current_weekly_dif - current_weekly_dea
                # print(f"周线MACD金叉信号出现日期: {current_date.strftime('%Y-%m-%d')}, DIF-DEA差值: {current_diff:.6f}")
        # else:
            # self.total_score -= self.weekly_macd_cross_weight
            # print(f"周线MACD无信号出现日期: {current_date.strftime('%Y-%m-%d')}, DIF-DEA差值: {current_diff:.6f}")
            # print(f"周线MACD无金叉:  -{self.weekly_macd_cross_weight}分")
        
        # 5. 检查日线EMA上穿月线EMA
        # 这里使用EMA20与月线EMA20的对比作为简化
        if self.data.Close[-1] > self.daily_ema[-1]:
            self.total_score += self.daily_ema_cross_weight
            # if hasattr(self, 'logger'):
            #     self.logger.info(f"当前日期: {current_date.strftime('%Y-%m-%d')},日线EMA上穿月线EMA: +{self.daily_ema_cross_weight}分，总分：{self.total_score}")
        else:
            self.total_score -= self.daily_ema_cross_weight
            # if hasattr(self, 'logger'):
            #     self.logger.info(f"当前日期: {current_date.strftime('%Y-%m-%d')},日线EMA下穿月线EMA: -{self.daily_ema_cross_weight}分，总分：{self.total_score}")
        
        # 记录当前得分
        # self.score_history.append(self.total_score)
        
        # 日终汇总打印，显示所有指标状态
        monthly_macd_value = self.monthly_macd.iloc[-1] if hasattr(self, 'monthly_macd') and self.monthly_macd is not None and len(self.monthly_macd) > 0 else "N/A"
        weekly_kdj_status = "金叉" if hasattr(self, 'weekly_kdj_golden_cross') and self.weekly_kdj_golden_cross else "无金叉"
        daily_ema_status = "上穿" if self.data.Close[-1] > self.daily_ema[-1] else "下穿"
        
        # self.logger.info(f"\n===== 交易日汇总: {current_date.strftime('%Y-%m-%d')} =====")
        # self.logger.info(f"\n 月线MACD值: {monthly_macd_value if isinstance(monthly_macd_value, str) else f'{monthly_macd_value:.4f}'}")
        # self.logger.info(f"\n 周线KDJ状态: {weekly_kdj_status}")
        # self.logger.info(f"\n 日线EMA状态: {daily_ema_status}")
        # self.logger.info(f"\n 评分结果: {self.total_score} (上涨趋势阈值: {self.buy_threshold}, 下跌趋势阈值: {self.sell_threshold})")
        # self.logger.info("===============================\n")


        # 根据月线MACD判断大趋势
        if hasattr(self, 'monthly_macd') and self.monthly_macd is not None and len(self.monthly_macd) > 0:
            current_monthly_macd = self.monthly_macd.iloc[-1]
            
            # 月线MACD大于0判断为上涨大趋势
            if current_monthly_macd > 0:
                if not self.in_uptrend:
                    self.in_uptrend = True
                    self.in_downtrend = False
                    if hasattr(self, 'logger'):
                        self.logger.info(f"进入上涨大趋势: 月线MACD = {current_monthly_macd:.4f} > 0 , 当前日期 ： {self.data.index[-1].strftime('%Y-%m-%d')}")
            # 月线MACD小于等于0判断为下跌大趋势
            else:
                if not self.in_downtrend:
                    self.in_downtrend = True
                    self.in_uptrend = False
                    if hasattr(self, 'logger'):
                        self.logger.info(f"进入下跌大趋势: 月线MACD = {current_monthly_macd:.4f} <= 0 ,  当前日期 ： {self.data.index[-1].strftime('%Y-%m-%d')}")

        # ===== 交易逻辑 =====·
        if not self.position:  # 没有持仓
            # 根据得分判断是否买入
            if self.total_score >= self.buy_threshold:
                # 计算止损和止盈价格
                self.stop_loss_price = price * (1 - self.stop_loss_pct)
                self.take_profit_price = price * (1 + self.take_profit_pct)
                # 开仓买入
                self.buy_signal = True
                self.sell_signal = False

                self.buy(size=self.position_size)
                if hasattr(self, 'logger'):
                    self.logger.info(f"得分买入信号({self.total_score}分): {self.data.index[-1].strftime('%Y-%m-%d')} 价格: {price:.2f}")
        
        else:  # 有持仓
            # 检查止损和止盈
            if price <= self.stop_loss_price:
                # 触发止损
                self.position.close()
                # print(f"止损卖出: {self.data.index[-1].strftime('%Y-%m-%d')} 价格: {price:.2f}")
            elif price >= self.take_profit_price:
                # 触发止盈
                self.position.close()
                # print(f"止盈卖出: {self.data.index[-1].strftime('%Y-%m-%d')} 价格: {price:.2f}")
            # 根据得分判断是否卖出
            elif self.total_score <= self.sell_threshold:
                # 部分卖出
                self.buy_signal = False
                self.sell_signal = True
                self.position.close(self.downtrend_exit_size)
                # print(f"得分卖出信号({self.total_score}分) {self.downtrend_exit_size*100}%: {self.data.index[-1].strftime('%Y-%m-%d')} 价格: {price:.2f}")
