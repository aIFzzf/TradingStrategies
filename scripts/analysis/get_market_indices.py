#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
获取主要市场指数数据
支持获取全球主要市场指数，包括美国、中国、欧洲等市场的主要指数
"""

import pandas as pd
import yfinance as yf
import argparse
from datetime import datetime, timedelta
import os
import json

# 主要市场指数代码映射
MARKET_INDICES = {
    # 美国市场
    "^GSPC": "标普500指数",
    "^DJI": "道琼斯工业平均指数",
    "^IXIC": "纳斯达克综合指数",
    "^RUT": "罗素2000指数",
    "^VIX": "芝加哥期权交易所波动率指数",
    
    # 中国市场
    "^SSE": "上证综合指数",
    "^SZSE": "深证成份指数",
    "^HSI": "恒生指数",
    "^HSCE": "恒生中国企业指数",
    "399006.SZ": "创业板指数",
    
    # 欧洲市场
    "^STOXX50E": "欧洲斯托克50指数",
    "^FTSE": "富时100指数",
    "^GDAXI": "德国DAX指数",
    "^FCHI": "法国CAC40指数",
    
    # 亚太市场
    "^N225": "日经225指数",
    "^KS11": "韩国KOSPI指数",
    "^AXJO": "澳大利亚ASX200指数",
    "^BSESN": "印度孟买SENSEX指数",
    
    # ETF指数
    "SPY": "SPDR标普500ETF",
    "QQQ": "纳斯达克100ETF",
    "IWM": "罗素2000ETF",
    "EEM": "新兴市场ETF",
    "FXI": "中国大型股ETF",
    
    # 加密货币
    "BTC-USD": "比特币",
    "ETH-USD": "以太坊",
    "BNB-USD": "币安币",
    "XRP-USD": "瑞波币",
    "ADA-USD": "艾达币",
    "SOL-USD": "索拉纳",
    "DOGE-USD": "狗狗币",
    "DOT-USD": "波卡币",
    "SHIB-USD": "柯基狗",
    "MATIC-USD": "Polygon"
}

# 指数分组
INDEX_GROUPS = {
    "us": ["^GSPC", "^DJI", "^IXIC", "^RUT", "^VIX"],
    "china": ["^SSE", "^SZSE", "^HSI", "^HSCE", "399006.SZ"],
    "europe": ["^STOXX50E", "^FTSE", "^GDAXI", "^FCHI"],
    "asia": ["^N225", "^KS11", "^AXJO", "^BSESN"],
    "etf": ["SPY", "QQQ", "IWM", "EEM", "FXI"],
    "crypto": ["BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD", "SOL-USD", "DOGE-USD", "DOT-USD", "SHIB-USD", "MATIC-USD"],
    "all": list(MARKET_INDICES.keys())
}

def get_index_data(index_symbol, start_date, end_date=None):
    """
    获取指定指数的历史数据
    
    参数:
        index_symbol (str): 指数代码
        start_date (str): 开始日期，格式为'YYYY-MM-DD'
        end_date (str, optional): 结束日期，格式为'YYYY-MM-DD'，默认为当前日期
        
    返回:
        pandas.DataFrame: 包含指数历史数据的DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # 获取指数数据
        index_data = yf.download(index_symbol, start=start_date, end=end_date)
        
        if len(index_data) == 0:
            print(f"警告: 无法获取指数 {index_symbol} 的数据")
            return None
        
        # 添加指数名称列
        index_name = MARKET_INDICES.get(index_symbol, index_symbol)
        index_data['Name'] = index_name
        
        # 添加Symbol列
        index_data['Symbol'] = index_symbol
        
        return index_data
    
    except Exception as e:
        print(f"获取指数 {index_symbol} 数据时出错: {e}")
        return None

def get_all_indices(group="all", start_date=None, end_date=None, save_dir=None):
    """
    获取指定组别的所有指数数据
    
    参数:
        group (str): 指数组别，可选值为'us', 'china', 'europe', 'asia', 'etf', 'all'
        start_date (str): 开始日期，格式为'YYYY-MM-DD'，默认为一年前
        end_date (str): 结束日期，格式为'YYYY-MM-DD'，默认为当前日期
        save_dir (str): 保存数据的目录，如果为None则不保存
        
    返回:
        dict: 包含所有指数数据的字典，键为指数代码，值为DataFrame
    """
    if start_date is None:
        # 默认获取一年的数据
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 获取指定组别的指数列表
    if group in INDEX_GROUPS:
        indices = INDEX_GROUPS[group]
    else:
        print(f"警告: 未知的指数组别 '{group}'，使用 'all' 组别")
        indices = INDEX_GROUPS["all"]
    
    # 获取所有指数数据
    indices_data = {}
    for symbol in indices:
        print(f"获取指数 {symbol} ({MARKET_INDICES.get(symbol, symbol)}) 的数据...")
        data = get_index_data(symbol, start_date, end_date)
        if data is not None and len(data) > 0:
            indices_data[symbol] = data
    
    # 保存数据到CSV文件
    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # 保存每个指数的数据
        for symbol, data in indices_data.items():
            file_path = os.path.join(save_dir, f"{symbol.replace('^', '')}_data_{timestamp}.csv")
            data.to_csv(file_path)
            print(f"已保存指数 {symbol} 的数据到 {file_path}")
        
        # 保存指数列表
        indices_list = [{
            "symbol": symbol,
            "name": MARKET_INDICES.get(symbol, symbol),
            "data_file": f"{symbol.replace('^', '')}_data_{timestamp}.csv"
        } for symbol in indices_data.keys()]
        
        indices_list_file = os.path.join(save_dir, f"indices_list_{group}_{timestamp}.json")
        with open(indices_list_file, 'w', encoding='utf-8') as f:
            json.dump(indices_list, f, ensure_ascii=False, indent=2)
        
        print(f"已保存指数列表到 {indices_list_file}")
    
    return indices_data

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="获取主要市场指数数据")
    parser.add_argument('--group', type=str, default='all', 
                        choices=['us', 'china', 'europe', 'asia', 'etf', 'crypto', 'all'],
                        help="指数组别，默认为'all'")
    
    parser.add_argument('--start_date', type=str, 
                        help="开始日期，格式为'YYYY-MM-DD'，默认为一年前")
    parser.add_argument('--end_date', type=str, 
                        help="结束日期，格式为'YYYY-MM-DD'，默认为当前日期")
    parser.add_argument('--save_dir', type=str, default='data/indices',
                        help="保存数据的目录，默认为'data/indices'")
    
    args = parser.parse_args()
    
    # 获取并保存指数数据
    indices_data = get_all_indices(
        group=args.group,
        start_date=args.start_date,
        end_date=args.end_date,
        save_dir=args.save_dir
    )
    
    print(f"成功获取 {len(indices_data)} 个指数的数据")

if __name__ == "__main__":
    main()
