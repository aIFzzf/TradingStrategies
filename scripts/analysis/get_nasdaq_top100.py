#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
获取纳斯达克前100的股票列表
"""

import pandas as pd
import requests
import json
import os
from bs4 import BeautifulSoup
import yfinance as yf


def get_nasdaq100_symbols():
    """
    获取纳斯达克100指数成分股列表
    
    返回:
    - list: 股票代码列表
    """
    try:
        # 方法1：使用维基百科获取纳斯达克100成分股
        url = "https://en.wikipedia.org/wiki/Nasdaq-100"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找包含成分股的表格
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables:
            if 'Ticker' in table.text:
                df = pd.read_html(str(table))[0]
                # 查找包含股票代码的列
                ticker_col = None
                for col in df.columns:
                    if 'Ticker' in col or 'Symbol' in col:
                        ticker_col = col
                        break
                
                if ticker_col:
                    # 提取股票代码列表
                    symbols = df[ticker_col].tolist()
                    # 过滤掉可能的非股票代码
                    symbols = [s for s in symbols if isinstance(s, str) and s.isalpha()]
                    return symbols
        
        # 如果方法1失败，尝试方法2
        print("方法1获取纳斯达克100成分股失败，尝试方法2...")
        
    except Exception as e:
        print(f"方法1获取纳斯达克100成分股出错: {e}")
    
    try:
        # 方法2：使用yfinance获取纳斯达克100指数成分股
        nasdaq100 = yf.Ticker('^NDX')
        # 获取指数成分股
        return nasdaq100.components
    except Exception as e:
        print(f"方法2获取纳斯达克100成分股出错: {e}")
    
    try:
        # 方法3：使用预定义的纳斯达克100成分股（如果前两种方法都失败）
        print("使用预定义的纳斯达克100成分股列表...")
        
        # 纳斯达克100主要成分股（截至2023年）
        predefined_nasdaq100 = [
            'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'META', 'TSLA', 'AVGO', 'PEP',
            'COST', 'CSCO', 'ADBE', 'NFLX', 'CMCSA', 'AMD', 'TMUS', 'INTC', 'INTU', 'QCOM',
            'TXN', 'AMGN', 'HON', 'AMAT', 'SBUX', 'MDLZ', 'ADI', 'PYPL', 'REGN', 'GILD',
            'ISRG', 'VRTX', 'PANW', 'KLAC', 'LRCX', 'SNPS', 'CDNS', 'ASML', 'MRVL', 'CTAS',
            'ABNB', 'FTNT', 'MNST', 'ORLY', 'ADSK', 'PCAR', 'PAYX', 'MCHP', 'CRWD', 'KDP',
            'KHC', 'AEP', 'DXCM', 'FAST', 'MRNA', 'CPRT', 'ODFL', 'EXC', 'BIIB', 'NXPI',
            'CHTR', 'ROST', 'IDXX', 'CTSH', 'DLTR', 'CSGP', 'XEL', 'EA', 'BKR', 'VRSK',
            'ANSS', 'TEAM', 'ILMN', 'WBD', 'FANG', 'EBAY', 'SIRI', 'ALGN', 'MTCH', 'ZS',
            'WDAY', 'LCID', 'RIVN', 'DASH', 'DDOG', 'OKTA', 'SPLK', 'ZM', 'DOCU', 'SGEN',
            'BKNG', 'CSX', 'MAR', 'AZN', 'JD', 'PDD', 'ATVI', 'MDB', 'TTD', 'RBLX'
        ]
        return predefined_nasdaq100
    except Exception as e:
        print(f"使用预定义的纳斯达克100成分股列表出错: {e}")
        return []


def save_symbols_to_file(symbols, filename='data/json/nasdaq100_symbols.json'):
    """
    将股票代码列表保存到文件
    
    参数:
    - symbols: list, 股票代码列表
    - filename: str, 文件名
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(symbols, f)
        print(f"已将{len(symbols)}个股票代码保存到 {filename}")
    except Exception as e:
        print(f"保存股票代码到文件时出错: {str(e)}")


def load_symbols_from_file(filename='data/json/nasdaq100_symbols.json'):
    """
    从文件加载股票代码列表
    
    参数:
    - filename: str, 文件名
    
    返回:
    - list: 股票代码列表
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                symbols = json.load(f)
            print(f"已从 {filename} 加载 {len(symbols)} 个股票代码")
            return symbols
        else:
            print(f"文件 {filename} 不存在")
            return []
    except Exception as e:
        print(f"从文件加载股票代码时出错: {str(e)}")
        return []


def main():
    """主函数"""
    # 获取纳斯达克100成分股
    symbols = get_nasdaq100_symbols()
    
    if symbols:
        print(f"成功获取 {len(symbols)} 个纳斯达克100成分股")
        
        # 保存到文件
        save_symbols_to_file(symbols)
        
        # 打印前10个股票代码
        print("前10个股票代码:")
        for i, symbol in enumerate(symbols[:10]):
            print(f"{i+1}. {symbol}")
    else:
        print("获取纳斯达克100成分股失败")


if __name__ == "__main__":
    main()
