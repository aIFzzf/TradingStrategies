#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
获取恒生科技指数前50的股票列表
"""

import pandas as pd
import requests
import json
import os
from bs4 import BeautifulSoup
import yfinance as yf
import re


def get_hstech50_symbols():
    """
    获取恒生科技指数成分股列表
    
    返回:
    - list: 股票代码列表（格式为：数字.HK）
    """
    try:
        # 方法1：从恒生官网获取
        url = "https://www.hsi.com.hk/eng/indexes/all-indexes/hstech"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找包含成分股的表格
        tables = soup.find_all('table')
        
        for table in tables:
            if 'Constituent' in table.text or '成分股' in table.text:
                df = pd.read_html(str(table))[0]
                
                # 查找包含股票代码的列
                code_col = None
                for col in df.columns:
                    if 'Code' in col or '代码' in col or 'Stock Code' in col:
                        code_col = col
                        break
                
                if code_col:
                    # 提取股票代码列表并格式化为 "数字.HK" 格式
                    symbols = []
                    for code in df[code_col]:
                        if isinstance(code, str):
                            # 提取数字部分
                            match = re.search(r'(\d+)', code)
                            if match:
                                symbols.append(f"{match.group(1)}.HK")
                        elif isinstance(code, int) or (isinstance(code, float) and code.is_integer()):
                            symbols.append(f"{int(code)}.HK")
                    
                    return symbols
        
        print("方法1获取恒生科技指数成分股失败，尝试方法2...")
        
    except Exception as e:
        print(f"方法1获取恒生科技指数成分股出错: {e}")
    
    try:
        # 方法2：从维基百科获取
        url = "https://en.wikipedia.org/wiki/Hang_Seng_Tech_Index"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找包含成分股的表格
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables:
            if 'Ticker' in table.text or 'Stock code' in table.text:
                df = pd.read_html(str(table))[0]
                
                # 查找包含股票代码的列
                code_col = None
                for col in df.columns:
                    if 'Ticker' in col or 'Code' in col or 'Stock code' in col:
                        code_col = col
                        break
                
                if code_col:
                    # 提取股票代码列表并格式化为 "数字.HK" 格式
                    symbols = []
                    for code in df[code_col]:
                        if isinstance(code, str):
                            # 提取数字部分
                            match = re.search(r'(\d+)', code)
                            if match:
                                symbols.append(f"{match.group(1)}.HK")
                        elif isinstance(code, int) or (isinstance(code, float) and code.is_integer()):
                            symbols.append(f"{int(code)}.HK")
                    
                    return symbols
        
        print("方法2获取恒生科技指数成分股失败，使用预定义列表...")
        
    except Exception as e:
        print(f"方法2获取恒生科技指数成分股出错: {e}")
    
    # 方法3：使用预定义的恒生科技指数成分股（截至2023年的数据）
    print("使用预定义的恒生科技指数成分股列表...")
    
    # 恒生科技指数主要成分股（可能需要更新）
    predefined_hstech = [
        '9618.HK',  # 京东集团-SW
        '9999.HK',  # 网易-S
        '9988.HK',  # 阿里巴巴-SW
        '0700.HK',  # 腾讯控股
        '3690.HK',  # 美团-W
        '9888.HK',  # 百度集团-SW
        '1024.HK',  # 快手-W
        '0981.HK',  # 中芯国际
        '9992.HK',  # 泡泡玛特
        '2382.HK',  # 舜宇光学科技
        '1810.HK',  # 小米集团-W
        '0268.HK',  # 金蝶国际
        '6618.HK',  # 京东健康
        '2269.HK',  # 药明生物
        '9626.HK',  # 哔哩哔哩-SW
        '1833.HK',  # 平安好医生
        '6969.HK',  # 思摩尔国际
        '2518.HK',  # 汇聚科技-W
        '1211.HK',  # 比亚迪股份
        '0992.HK',  # 联想集团
        '9633.HK',  # 农夫山泉
        '2015.HK',  # 理想汽车-W
        '9868.HK',  # 小鹏汽车-W
        '9866.HK',  # 蔚来-SW
        '9961.HK',  # 旷视科技-W
        '6699.HK',  # 时代电气
        '0772.HK',  # 阅文集团
        '2400.HK',  # 心动公司
        '1797.HK',  # 新东方在线
        '9996.HK',  # 沪江教育
    ]
    
    return predefined_hstech


def save_symbols_to_file(symbols, filename='data/json/hstech50_symbols.json'):
    """
    将股票代码列表保存到文件
    
    参数:
    - symbols: list, 股票代码列表
    - filename: str, 文件名
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    try:
        with open(filename, 'w') as f:
            json.dump(symbols, f)
        print(f"已将{len(symbols)}个股票代码保存到 {filename}")
    except Exception as e:
        print(f"保存股票代码到文件出错: {e}")


def load_symbols_from_file(filename='data/json/hstech50_symbols.json'):
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
        print(f"从文件加载股票代码出错: {e}")
        return []


def main():
    """主函数"""
    # 获取恒生科技指数成分股
    symbols = get_hstech50_symbols()
    
    if symbols:
        print(f"成功获取 {len(symbols)} 个恒生科技指数成分股")
        
        # 保存到文件
        save_symbols_to_file(symbols)
        
        # 打印前10个股票代码
        print("前10个股票代码:")
        for i, symbol in enumerate(symbols[:10]):
            print(f"{i+1}. {symbol}")
    else:
        print("获取恒生科技指数成分股失败")


if __name__ == "__main__":
    main()
