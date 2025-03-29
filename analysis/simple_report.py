#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版交易策略回测结果分析和报表生成模块
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


def generate_simple_report(strategy_name, symbol, results_dir='data/csv', output_dir='reports'):
    """
    生成简单的策略分析报表
    
    Parameters:
        strategy_name (str): 策略名称
        symbol (str): 股票代码
        results_dir (str): 回测结果CSV文件所在目录
        output_dir (str): 报表输出目录
        
    Returns:
        str: 报告文件路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 构建文件名
    file_name = f"{strategy_name}_{symbol}_results.csv"
    file_path = os.path.join(results_dir, file_name)
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误: 找不到回测结果文件: {file_path}")
        return None
    
    try:
        # 加载回测结果
        results = pd.read_csv(file_path)
        
        # 生成报告HTML
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{strategy_name} 策略分析报表 - {symbol}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>{strategy_name} 策略分析报表</h1>
            <p>股票代码: {symbol}</p>
            <p>分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>回测结果</h2>
            <table>
                <tr>
        """
        
        # 添加表头
        for col in results.columns:
            report_html += f"<th>{col}</th>"
        
        report_html += """
                </tr>
        """
        
        # 添加数据行
        for _, row in results.iterrows():
            report_html += "<tr>"
            for value in row:
                if isinstance(value, (int, float)):
                    report_html += f"<td>{value:.4f}</td>"
                else:
                    report_html += f"<td>{value}</td>"
            report_html += "</tr>"
        
        report_html += """
            </table>
            
            <h2>分析结论</h2>
            <p>
                这是一个简化版的策略分析报表，展示了回测结果的基本数据。
                如需更详细的分析，请使用完整版的报表生成器。
            </p>
        </body>
        </html>
        """
        
        # 保存报告
        report_path = os.path.join(output_dir, f"{strategy_name}_{symbol}_simple_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
            
        print(f"简单报告已生成并保存到: {report_path}")
        
        return report_path
    
    except Exception as e:
        print(f"生成报告时出错: {str(e)}")
        return None


def compare_simple(strategy_names, symbol, results_dir='data/csv', output_dir='reports'):
    """
    简单比较多个策略的性能
    
    Parameters:
        strategy_names (list): 策略名称列表
        symbol (str): 股票代码
        results_dir (str): 回测结果CSV文件所在目录
        output_dir (str): 报表输出目录
        
    Returns:
        str: 报告文件路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载各个策略的结果
    results = {}
    
    for strategy in strategy_names:
        file_path = os.path.join(results_dir, f"{strategy}_{symbol}_results.csv")
        
        if os.path.exists(file_path):
            try:
                results[strategy] = pd.read_csv(file_path)
            except Exception as e:
                print(f"加载 {strategy} 策略结果时出错: {str(e)}")
    
    if not results:
        print("没有找到任何策略结果")
        return None
    
    # 生成比较报告HTML
    report_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>策略比较报表 - {symbol}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h1>策略比较报表</h1>
        <p>股票代码: {symbol}</p>
        <p>分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>策略性能比较</h2>
        <table>
            <tr>
                <th>指标</th>
    """
    
    # 添加策略名称作为表头
    for strategy in results:
        report_html += f"<th>{strategy}</th>"
    
    report_html += """
            </tr>
    """
    
    # 尝试添加常见指标
    common_metrics = ['Return [%]', 'Max. Drawdown [%]', 'Sharpe Ratio', '# Trades', 'Win Rate [%]']
    
    for metric in common_metrics:
        report_html += f"<tr><td>{metric}</td>"
        
        for strategy in results:
            if metric in results[strategy].columns:
                value = results[strategy][metric].values[0]
                report_html += f"<td>{value:.4f}</td>"
            else:
                report_html += "<td>N/A</td>"
        
        report_html += "</tr>"
    
    report_html += """
        </table>
        
        <h2>分析结论</h2>
        <p>
            这是一个简化版的策略比较报表，展示了各个策略的基本性能指标。
            如需更详细的分析，请使用完整版的报表生成器。
        </p>
    </body>
    </html>
    """
    
    # 保存报告
    report_path = os.path.join(output_dir, f"strategy_comparison_{symbol}_simple.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_html)
        
    print(f"简单比较报告已生成并保存到: {report_path}")
    
    return report_path


if __name__ == "__main__":
    # 示例用法
    generate_simple_report('dual_ma', 'AAPL')
    
    # 比较多个策略
    compare_simple(['dual_ma', 'macd', 'bollinger'], 'AAPL')
