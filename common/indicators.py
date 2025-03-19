#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
技术指标计算工具
提供各种常用技术指标的计算函数
"""

import pandas as pd
import numpy as np


def SMA(values, period):
    """
    计算简单移动平均线
    
    参数:
    - values: 价格序列
    - period: 周期
    
    返回:
    - SMA序列
    """
    return pd.Series(values).rolling(period).mean()


def EMA(values, period):
    """
    计算指数移动平均线
    
    参数:
    - values: 价格序列
    - period: 周期
    
    返回:
    - EMA序列
    """
    return pd.Series(values).ewm(span=period, adjust=False).mean()


def MACD(values, fast_period=12, slow_period=26, signal_period=9):
    """
    计算MACD指标
    
    参数:
    - values: 价格序列
    - fast_period: 快速EMA周期，默认12
    - slow_period: 慢速EMA周期，默认26
    - signal_period: 信号线周期，默认9
    
    返回:
    - dif: DIF线 (快速EMA - 慢速EMA)
    - dea: DEA线 (DIF的EMA)
    - macd: MACD柱状图 (DIF - DEA) * 2
    """
    # 转换为pandas Series
    close = pd.Series(values)
    
    # 计算快速和慢速EMA
    fast_ema = EMA(close, fast_period)
    slow_ema = EMA(close, slow_period)
    
    # 计算DIF线
    dif = fast_ema - slow_ema
    
    # 计算DEA线
    dea = EMA(dif, signal_period)
    
    # 计算MACD柱状图，标准公式是 (DIF - DEA) * 2
    macd = (dif - dea) * 2
    
    return dif, dea, macd


def RSI(values, period=14):
    """
    计算相对强弱指数(RSI)
    
    参数:
    - values: 价格序列
    - period: 周期，默认14
    
    返回:
    - RSI序列
    """
    # 转换为pandas Series
    close = pd.Series(values)
    
    # 计算价格变化
    delta = close.diff()
    
    # 分离上涨和下跌
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # 计算平均上涨和下跌
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # 计算相对强度
    rs = avg_gain / avg_loss
    
    # 计算RSI
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def BBANDS(values, period=20, std_dev=2):
    """
    计算布林带
    
    参数:
    - values: 价格序列
    - period: 周期，默认20
    - std_dev: 标准差倍数，默认2
    
    返回:
    - upper_band: 上轨
    - middle_band: 中轨
    - lower_band: 下轨
    """
    # 转换为pandas Series
    close = pd.Series(values)
    
    # 计算中轨(SMA)
    middle_band = SMA(close, period)
    
    # 计算标准差
    std = close.rolling(window=period).std()
    
    # 计算上轨和下轨
    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)
    
    return upper_band, middle_band, lower_band


def ATR(high, low, close, period=14):
    """
    计算平均真实范围(ATR)
    
    参数:
    - high: 最高价序列
    - low: 最低价序列
    - close: 收盘价序列
    - period: 周期，默认14
    
    返回:
    - ATR序列
    """
    # 转换为pandas Series
    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)
    
    # 计算前一天收盘价
    prev_close = close.shift(1)
    
    # 计算真实范围
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    # 取三者中的最大值
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # 计算ATR
    atr = tr.rolling(window=period).mean()
    
    return atr


def STOCH(high, low, close, k_period=14, d_period=3, slowing=3):
    """
    计算随机指标(KD)
    
    参数:
    - high: 最高价序列
    - low: 最低价序列
    - close: 收盘价序列
    - k_period: K值周期，默认14
    - d_period: D值周期，默认3
    - slowing: 慢速周期，默认3
    
    返回:
    - k: K值
    - d: D值
    """
    # 转换为pandas Series
    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)
    
    # 计算最高价和最低价
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    # 计算%K
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    
    # 计算慢速%K
    if slowing > 1:
        k = k.rolling(window=slowing).mean()
    
    # 计算%D
    d = k.rolling(window=d_period).mean()
    
    return k, d


def OBV(close, volume):
    """
    计算能量潮指标(OBV)
    
    参数:
    - close: 收盘价序列
    - volume: 成交量序列
    
    返回:
    - OBV序列
    """
    # 转换为pandas Series
    close = pd.Series(close)
    volume = pd.Series(volume)
    
    # 计算价格变化方向
    direction = np.where(close > close.shift(1), 1, np.where(close < close.shift(1), -1, 0))
    
    # 计算OBV
    obv = (direction * volume).cumsum()
    
    return obv


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


def KDJ(high, low, close, k_period=9, d_period=3, j_period=3):
    """
    计算KDJ指标
    
    参数:
    - high: 最高价序列
    - low: 最低价序列
    - close: 收盘价序列
    - k_period: K值周期，默认9
    - d_period: D值周期，默认3
    - j_period: J值周期，默认3
    
    返回:
    - k: K值
    - d: D值
    - j: J值
    """
    # 转换为pandas Series
    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)
    
    # 计算最高价和最低价
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    # 计算RSV
    rsv = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    
    # 初始化K、D值
    k = pd.Series(index=close.index, dtype=float)
    d = pd.Series(index=close.index, dtype=float)
    
    # 填充前k_period个值为NaN
    k[:k_period-1] = np.nan
    d[:k_period-1] = np.nan
    
    # 设置初始值（第k_period个值）
    first_valid_idx = k_period-1
    if first_valid_idx < len(rsv):
        k.iloc[first_valid_idx] = rsv.iloc[first_valid_idx]
        d.iloc[first_valid_idx] = rsv.iloc[first_valid_idx]
    
    # 计算K、D值
    for i in range(k_period, len(close)):
        k.iloc[i] = 2/3 * k.iloc[i-1] + 1/3 * rsv.iloc[i]
        d.iloc[i] = 2/3 * d.iloc[i-1] + 1/3 * k.iloc[i]
    
    # 计算J值
    j = 3 * k - 2 * d
    
    return k, d, j
