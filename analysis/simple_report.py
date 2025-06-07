#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版交易策略回测结果分析和报表生成模块
支持策略回测结果、纳斯达克100和恒生科技50指数成分股分析报表生成
"""

import os
import csv
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 英文列名到中文列名的映射
COLUMN_TRANSLATIONS = {
    'Symbol': '股票代码',
    'Name': '名称',
    'Price': '价格',
    'Return [%]': '收益率 [%]',
    'Buy Signal': '买入信号',
    'Sell Signal': '卖出信号',
    'In Uptrend': '处于上升趋势',
    'Notes': '备注'
}


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


def generate_html_table(data, headers=None, columns=None):
    """
    生成HTML表格
    
    Parameters:
        data (list or pd.DataFrame): 数据列表或DataFrame
        headers (list, optional): 列名列表，当data为list时使用
        columns (list, optional): 要显示的列名列表
        
    Returns:
        str: HTML表格
    """
    if isinstance(data, pd.DataFrame):
        # 如果是DataFrame，转换为列表格式
        if columns is None:
            columns = data.columns.tolist()
        
        headers = columns
        rows = []
        for _, row in data.iterrows():
            rows.append([row[col] for col in columns])
        data = rows
    else:
        # 如果是列表，确保headers存在
        if headers is None:
            raise ValueError("当data为列表时，必须提供headers参数")
        
        if columns is None:
            columns = headers
    
    if not data:
        return "<p>没有数据</p>"
    
    # 获取列索引
    if isinstance(data[0], list):
        col_indices = [headers.index(col) for col in columns if col in headers]
    else:
        col_indices = range(len(columns))
    
    html = "<table border='1' cellpadding='5' cellspacing='0' style='width:100%;'>\n"
    
    # 添加表头
    html += "  <tr>\n"
    for col in columns:
        if col in headers:
            # 使用中文列名
            col_display = COLUMN_TRANSLATIONS.get(col, col)
            html += f"    <th>{col_display}</th>\n"
    html += "  </tr>\n"
    
    # 添加数据行
    for row in data:
        # 检查是否是上涨趋势且有买入信号的股票
        is_uptrend_with_buy_signal = False
        buy_signal_idx = -1
        uptrend_idx = -1
        
        if 'Buy Signal' in columns and 'In Uptrend' in columns:
            buy_signal_idx = columns.index('Buy Signal')
            uptrend_idx = columns.index('In Uptrend')
            
            if buy_signal_idx < len(col_indices) and uptrend_idx < len(col_indices):
                buy_signal_col_idx = col_indices[buy_signal_idx]
                uptrend_col_idx = col_indices[uptrend_idx]
                
                if (buy_signal_col_idx < len(row) and uptrend_col_idx < len(row) and 
                    row[buy_signal_col_idx] == 'Yes' and row[uptrend_col_idx] == 'Yes'):
                    is_uptrend_with_buy_signal = True
        
        # 根据条件设置行样式
        if is_uptrend_with_buy_signal:
            html += "  <tr style='color: red; font-weight: bold;'>\n"
        else:
            html += "  <tr>\n"
            
        for i, idx in enumerate(col_indices):
            if idx < len(row):
                value = row[idx]
                col_name = columns[i] if i < len(columns) else ""
                
                if col_name == 'Return [%]' and isinstance(value, (int, float)):
                    html += f"    <td>{value:.2f}%</td>\n"
                elif col_name in ['Buy Signal', 'Sell Signal', 'In Uptrend'] and value in ['Yes', 'No']:
                    # 翻译Yes/No
                    translated_value = "是" if value == "Yes" else "否"
                    html += f"    <td>{translated_value}</td>\n"
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    html += f"    <td>{value:.4f}</td>\n"
                else:
                    html += f"    <td>{value}</td>\n"
            else:
                html += "    <td>N/A</td>\n"
        html += "  </tr>\n"
    
    html += "</table>"
    return html


def load_index_data(file_path):
    """
    加载指数成分股分析数据
    
    Parameters:
        file_path (str): 分析数据CSV文件路径
        
    Returns:
        list: 分析数据列表
        list: 列名列表
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到分析数据文件: {file_path}")
    
    data = []
    headers = []
    
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # 获取表头
        for row in reader:
            data.append(row)
    
    return data, headers


def calculate_summary_stats(data, headers):
    """
    计算汇总统计数据
    
    Parameters:
        data (list): 分析数据列表
        headers (list): 列名列表
        
    Returns:
        dict: 汇总统计数据
    """
    # 获取列索引
    date_idx = headers.index('Date') if 'Date' in headers else 0
    symbol_idx = headers.index('Symbol') if 'Symbol' in headers else 1
    buy_signal_idx = headers.index('Buy Signal') if 'Buy Signal' in headers else 4
    sell_signal_idx = headers.index('Sell Signal') if 'Sell Signal' in headers else 5
    return_idx = headers.index('Return [%]') if 'Return [%]' in headers else 6
    uptrend_idx = headers.index('In Uptrend') if 'In Uptrend' in headers else 7
    
    # 计算统计数据
    symbols = set()
    buy_signals = []
    sell_signals = []
    uptrend_stocks = []
    returns = []
    
    for row in data:
        symbols.add(row[symbol_idx])
        
        # 转换收益率为浮点数
        try:
            return_val = float(row[return_idx])
            returns.append(return_val)
        except (ValueError, TypeError):
            pass
        
        if row[buy_signal_idx] == 'Yes':
            buy_signals.append(row)
        
        if row[sell_signal_idx] == 'Yes':
            sell_signals.append(row)
            
        if row[uptrend_idx] == 'Yes':
            uptrend_stocks.append(row)
    
    # 计算平均收益率
    avg_return = sum(returns) / len(returns) if returns else 0
    max_return = max(returns) if returns else 0
    min_return = min(returns) if returns else 0
    
    # 获取最新日期
    latest_date = data[0][date_idx] if data else datetime.now().strftime('%Y-%m-%d')
    
    return {
        '总股票数': len(symbols),
        '买入信号股票数': len(buy_signals),
        '卖出信号股票数': len(sell_signals),
        '上升趋势股票数': len(uptrend_stocks),
        '平均收益率': avg_return,
        '最高收益率': max_return,
        '最低收益率': min_return,
        '最新日期': latest_date,
        '买入信号股票': buy_signals,
        '卖出信号股票': sell_signals
    }


def sort_data_by_return(data, headers, ascending=False, limit=10):
    """
    按收益率排序数据
    
    Parameters:
        data (list): 分析数据列表
        headers (list): 列名列表
        ascending (bool): 是否升序排序
        limit (int): 限制返回的行数
        
    Returns:
        list: 排序后的数据列表
    """
    return_idx = headers.index('Return [%]') if 'Return [%]' in headers else 6
    
    # 转换收益率为浮点数并排序
    sorted_data = []
    for row in data:
        try:
            return_val = float(row[return_idx])
            sorted_data.append((return_val, row))
        except (ValueError, TypeError):
            pass
    
    sorted_data.sort(key=lambda x: x[0], reverse=not ascending)
    
    # 返回排序后的行数据（不包含排序键）
    return [row for _, row in sorted_data[:limit]]


def generate_nasdaq100_report(data_file='data/analysis/nasdaq100_analysis.csv', output_dir='reports'):
    """
    生成纳斯达克100指数成分股分析报表
    
    Parameters:
        data_file (str): 分析数据CSV文件路径
        output_dir (str): 报表输出目录
        
    Returns:
        str: 报告文件路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 加载分析数据
        data, headers = load_index_data(data_file)
        
        # 计算统计数据
        stats = calculate_summary_stats(data, headers)
        
        # 获取表现最好和最差的股票
        top_performers = sort_data_by_return(data, headers, ascending=False, limit=10)
        bottom_performers = sort_data_by_return(data, headers, ascending=True, limit=10)
        
        # 生成报告HTML
        report_date = datetime.now().strftime('%Y%m%d')
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>纳斯达克100指数成分股分析报表</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .summary {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .buy {{ color: green; }}
                .sell {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>纳斯达克100指数成分股分析报表</h1>
            <p>分析日期: {stats['最新日期']}</p>
            <p>报表生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>市场概览</h2>
            <div class="summary">
                <p>总股票数: <strong>{stats['总股票数']}</strong></p>
                <p>买入信号股票数: <strong class="buy">{stats['买入信号股票数']}</strong></p>
                <p>卖出信号股票数: <strong class="sell">{stats['卖出信号股票数']}</strong></p>
                <p>处于上升趋势股票数: <strong>{stats['上升趋势股票数']}</strong></p>
                <p>平均收益率: <strong>{stats['平均收益率']:.2f}%</strong></p>
                <p>最高收益率: <strong>{stats['最高收益率']:.2f}%</strong></p>
                <p>最低收益率: <strong>{stats['最低收益率']:.2f}%</strong></p>
            </div>
            
            <h2>买入信号</h2>
            {generate_html_table(stats['买入信号股票'], headers, columns=['Symbol', 'Name', 'Price', 'Return [%]', 'In Uptrend', 'Notes'])}
            
            <h2>卖出信号</h2>
            {generate_html_table(stats['卖出信号股票'], headers, columns=['Symbol', 'Name', 'Price', 'Return [%]', 'In Uptrend', 'Notes'])}
            
            <h2>表现最佳的10只股票</h2>
            {generate_html_table(top_performers, headers, columns=['Symbol', 'Name', 'Price', 'Return [%]', 'Buy Signal', 'Sell Signal', 'In Uptrend'])}
            
            <h2>表现最差的10只股票</h2>
            {generate_html_table(bottom_performers, headers, columns=['Symbol', 'Name', 'Price', 'Return [%]', 'Buy Signal', 'Sell Signal', 'In Uptrend'])}
            
            <h2>投资建议</h2>
            <p>
                根据当前市场分析，建议关注具有买入信号且处于上升趋势的股票，特别是那些收益率较高的股票。
                同时，考虑减持或避开有卖出信号且不在上升趋势的股票。
            </p>
            
            <h2>免责声明</h2>
            <p>
                本报告仅供参考，不构成投资建议。投资决策应基于个人风险承受能力和投资目标。
                过往表现不代表未来收益。
            </p>
        </body>
        </html>
        """
        
        # 保存报告
        report_path = os.path.join(output_dir, f"nasdaq100_analysis_{report_date}.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
            
        print(f"纳斯达克100指数成分股分析报表已生成并保存到: {report_path}")
        
        return report_path
    
    except Exception as e:
        print(f"生成纳斯达克100指数成分股分析报表时出错: {str(e)}")
        return None


def generate_hstech50_report(data_file='data/analysis/hstech50_analysis.csv', output_dir='reports'):
    """
    生成恒生科技50指数成分股分析报表
    
    Parameters:
        data_file (str): 分析数据CSV文件路径
        output_dir (str): 报表输出目录
        
    Returns:
        str: 报告文件路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 加载分析数据
        data, headers = load_index_data(data_file)
        
        # 计算统计数据
        stats = calculate_summary_stats(data, headers)
        
        # 获取表现最好和最差的股票
        top_performers = sort_data_by_return(data, headers, ascending=False, limit=10)
        bottom_performers = sort_data_by_return(data, headers, ascending=True, limit=10)
        
        # 生成报告HTML
        report_date = datetime.now().strftime('%Y%m%d')
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>恒生科技50指数成分股分析报表</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .summary {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .buy {{ color: green; }}
                .sell {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>恒生科技50指数成分股分析报表</h1>
            <p>分析日期: {stats['最新日期']}</p>
            <p>报表生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>市场概览</h2>
            <div class="summary">
                <p>总股票数: <strong>{stats['总股票数']}</strong></p>
                <p>买入信号股票数: <strong class="buy">{stats['买入信号股票数']}</strong></p>
                <p>卖出信号股票数: <strong class="sell">{stats['卖出信号股票数']}</strong></p>
                <p>处于上升趋势股票数: <strong>{stats['上升趋势股票数']}</strong></p>
                <p>平均收益率: <strong>{stats['平均收益率']:.2f}%</strong></p>
                <p>最高收益率: <strong>{stats['最高收益率']:.2f}%</strong></p>
                <p>最低收益率: <strong>{stats['最低收益率']:.2f}%</strong></p>
            </div>
            
            <h2>买入信号</h2>
            {generate_html_table(stats['买入信号股票'], headers, columns=['Symbol', 'Name', 'Price', 'Return [%]', 'In Uptrend', 'Notes'])}
            
            <h2>卖出信号</h2>
            {generate_html_table(stats['卖出信号股票'], headers, columns=['Symbol', 'Name', 'Price', 'Return [%]', 'In Uptrend', 'Notes'])}
            
            <h2>表现最佳的10只股票</h2>
            {generate_html_table(top_performers, headers, columns=['Symbol', 'Name', 'Price', 'Return [%]', 'Buy Signal', 'Sell Signal', 'In Uptrend'])}
            
            <h2>表现最差的10只股票</h2>
            {generate_html_table(bottom_performers, headers, columns=['Symbol', 'Name', 'Price', 'Return [%]', 'Buy Signal', 'Sell Signal', 'In Uptrend'])}
            
            <h2>投资建议</h2>
            <p>
                根据当前市场分析，建议关注具有买入信号且处于上升趋势的股票，特别是那些收益率较高的股票。
                同时，考虑减持或避开有卖出信号且不在上升趋势的股票。
            </p>
            
            <h2>免责声明</h2>
            <p>
                本报告仅供参考，不构成投资建议。投资决策应基于个人风险承受能力和投资目标。
                过往表现不代表未来收益。
            </p>
        </body>
        </html>
        """
        
        # 保存报告
        report_path = os.path.join(output_dir, f"hstech50_analysis_{report_date}.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
            
        print(f"恒生科技50指数成分股分析报表已生成并保存到: {report_path}")
        
        return report_path
    
    except Exception as e:
        print(f"生成恒生科技50指数成分股分析报表时出错: {str(e)}")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python simple_report.py [report_type] [options]")
        print("报表类型:")
        print("  strategy - 生成策略回测报表")
        print("  nasdaq100 - 生成纳斯达克100指数成分股分析报表")
        print("  hstech50 - 生成恒生科技50指数成分股分析报表")
        print("  compare - 比较多个策略")
        sys.exit(1)
    
    report_type = sys.argv[1]
    
    if report_type == "strategy":
        if len(sys.argv) < 4:
            print("用法: python simple_report.py strategy [strategy_name] [symbol]")
            sys.exit(1)
        strategy_name = sys.argv[2]
        symbol = sys.argv[3]
        generate_simple_report(strategy_name, symbol)
    
    elif report_type == "nasdaq100":
        data_file = sys.argv[2] if len(sys.argv) > 2 else 'data/analysis/nasdaq100_analysis.csv'
        generate_nasdaq100_report(data_file)
    
    elif report_type == "hstech50":
        data_file = sys.argv[2] if len(sys.argv) > 2 else 'data/analysis/hstech50_analysis.csv'
        generate_hstech50_report(data_file)
    
    elif report_type == "compare":
        if len(sys.argv) < 4:
            print("用法: python simple_report.py compare [symbol] [strategy1] [strategy2] ...")
            sys.exit(1)
        symbol = sys.argv[2]
        strategies = sys.argv[3:]
        compare_simple(strategies, symbol)
    
    else:
        print(f"未知的报表类型: {report_type}")
        print("可用的报表类型: strategy, nasdaq100, hstech50, compare")
        sys.exit(1)
