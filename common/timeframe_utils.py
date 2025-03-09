#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
时间周期转换工具
提供日线数据转换为周线、月线等不同周期的功能
"""

import pandas as pd
import numpy as np


def resample_to_weekly(data):
    """
    将日线数据重采样为周线数据
    
    参数:
    - data: DataFrame, 包含OHLCV数据的DataFrame，索引为日期
    
    返回:
    - DataFrame, 重采样后的周线数据
    """
    # 确保索引是日期类型
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("数据索引必须是日期类型")
    
    # 进行重采样
    weekly = data.resample('W').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    
    # 删除缺失值
    weekly = weekly.dropna()
    
    return weekly


def resample_to_monthly(data):
    """
    将日线数据重采样为月线数据
    
    参数:
    - data: DataFrame, 包含OHLCV数据的DataFrame，索引为日期
    
    返回:
    - DataFrame, 重采样后的月线数据
    """
    # 确保索引是日期类型
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("数据索引必须是日期类型")
    
    # 进行重采样 (使用'ME'替代已弃用的'M')
    monthly = data.resample('ME').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    
    # 删除缺失值
    monthly = monthly.dropna()
    
    return monthly


def resample_to_timeframe(data, timeframe):
    """
    将数据重采样为指定的时间周期
    
    参数:
    - data: DataFrame, 包含OHLCV数据的DataFrame，索引为日期
    - timeframe: str, 目标时间周期，可选值：
      - 'D': 日线 (保持原样)
      - 'W': 周线
      - 'M': 月线
      - 'Q': 季线
      - 'Y': 年线
    
    返回:
    - DataFrame, 重采样后的数据
    """
    # 如果是日线或无效值，直接返回原数据
    if timeframe.upper() not in ['W', 'M', 'Q', 'Y']:
        return data.copy()
    
    # 确保索引是日期类型
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("数据索引必须是日期类型")
    
    # 进行重采样
    resampled = data.resample(timeframe).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    
    # 删除缺失值
    resampled = resampled.dropna()
    
    return resampled


def map_higher_timeframe_to_daily(daily_data, higher_tf_series):
    """
    将高周期数据映射到日线数据
    
    参数:
    - daily_data: DataFrame, 日线数据
    - higher_tf_series: Series, 高周期数据
    
    返回:
    - Series: 映射到日线的高周期数据
    """
    # 创建一个与日线数据索引相同的空Series
    daily_index = daily_data.index
    result = pd.Series(index=daily_index, dtype=float)
    
    # 对于每个日期，找到对应的高周期数据
    for date in daily_index:
        # 找到日期之前的最后一个高周期数据点
        mask = higher_tf_series.index <= date
        if mask.any():
            last_value = higher_tf_series[mask].iloc[-1]
            result[date] = last_value
    
    # 前向填充缺失值 (使用ffill()替代已弃用的method='ffill')
    result = result.ffill()
    
    return result


def calculate_ma(data, period, column='Close'):
    """
    计算移动平均线
    
    参数:
    - data: DataFrame, 包含价格数据的DataFrame
    - period: int, 移动平均周期
    - column: str, 要计算移动平均的列名，默认为'Close'
    
    返回:
    - Series, 移动平均线
    """
    return data[column].rolling(period).mean()


def get_timeframe_data(daily_data, timeframe='D'):
    """
    获取指定时间周期的数据
    
    参数:
    - daily_data: DataFrame, 日线数据
    - timeframe: str, 目标时间周期，可选值：'D', 'W', 'M'
    
    返回:
    - DataFrame, 指定时间周期的数据
    """
    if timeframe.upper() == 'D':
        return daily_data.copy()
    elif timeframe.upper() == 'W':
        return resample_to_weekly(daily_data)
    elif timeframe.upper() == 'M':
        return resample_to_monthly(daily_data)
    else:
        raise ValueError(f"不支持的时间周期: {timeframe}，支持的值为: 'D', 'W', 'M'")


def align_timeframes(daily_data, weekly_data=None, monthly_data=None):
    """
    将不同周期的数据对齐到日线时间轴
    
    参数:
    - daily_data: DataFrame, 日线数据
    - weekly_data: DataFrame, 周线数据，可选
    - monthly_data: DataFrame, 月线数据，可选
    
    返回:
    - dict, 包含对齐后的数据：
      - 'daily': 原日线数据
      - 'weekly': 对齐到日线的周线数据
      - 'monthly': 对齐到日线的月线数据
    """
    result = {'daily': daily_data}
    
    # 对齐周线数据
    if weekly_data is not None:
        weekly_aligned = {}
        for column in weekly_data.columns:
            weekly_aligned[column] = map_higher_timeframe_to_daily(daily_data, weekly_data[column])
        result['weekly'] = pd.DataFrame(weekly_aligned, index=daily_data.index)
    
    # 对齐月线数据
    if monthly_data is not None:
        monthly_aligned = {}
        for column in monthly_data.columns:
            monthly_aligned[column] = map_higher_timeframe_to_daily(daily_data, monthly_data[column])
        result['monthly'] = pd.DataFrame(monthly_aligned, index=daily_data.index)
    
    return result
