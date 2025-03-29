#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交易策略回测结果分析和报表生成模块
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json
from pathlib import Path
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号


class ReportGenerator:
    """交易策略回测结果分析和报表生成类"""
    
    def __init__(self, results_dir='data/csv', output_dir='reports'):
        """
        初始化报表生成器
        
        Parameters:
            results_dir (str): 回测结果CSV文件所在目录
            output_dir (str): 报表输出目录
        """
        self.results_dir = results_dir
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
    def load_results(self, file_path):
        """
        加载回测结果文件
        
        Parameters:
            file_path (str): 回测结果CSV文件路径
            
        Returns:
            pd.DataFrame: 回测结果数据
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"找不到回测结果文件: {file_path}")
        
        return pd.read_csv(file_path)
    
    def load_nasdaq100_analysis(self, file_path):
        """
        加载纳斯达克100指数成分股分析数据
        
        Parameters:
            file_path (str): 分析数据CSV文件路径
            
        Returns:
            pd.DataFrame: 分析数据
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"找不到分析数据文件: {file_path}")
        
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 转换日期列为日期类型
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            
        return df
    
    def load_all_results(self, strategy_type=None):
        """
        加载指定策略类型的所有回测结果
        
        Parameters:
            strategy_type (str, optional): 策略类型，如 'dual_ma', 'macd' 等
            
        Returns:
            dict: 策略名称到回测结果的映射
        """
        results = {}
        
        for file in os.listdir(self.results_dir):
            if not file.endswith('.csv'):
                continue
                
            if strategy_type and not file.startswith(strategy_type):
                continue
                
            file_path = os.path.join(self.results_dir, file)
            strategy_name = file.split('_')[0]
            symbol = file.split('_')[1]
            
            if strategy_name not in results:
                results[strategy_name] = {}
                
            results[strategy_name][symbol] = self.load_results(file_path)
            
        return results
    
    def calculate_metrics(self, results):
        """
        计算额外的性能指标
        
        Parameters:
            results (pd.DataFrame): 回测结果数据
            
        Returns:
            pd.DataFrame: 增强的回测结果数据
        """
        # 复制结果以避免修改原始数据
        enhanced_results = results.copy()
        
        # 计算风险调整后收益
        if 'Return [%]' in enhanced_results.columns and 'Max. Drawdown [%]' in enhanced_results.columns:
            enhanced_results['风险调整后收益'] = enhanced_results['Return [%]'] / abs(enhanced_results['Max. Drawdown [%]'])
        
        # 计算平均交易收益率（如果有交易数据）
        if '# Trades' in enhanced_results.columns and 'Return [%]' in enhanced_results.columns:
            enhanced_results['平均每笔交易收益'] = enhanced_results['Return [%]'] / enhanced_results['# Trades']
        
        # 计算年化收益率（如果有开始和结束日期）
        if 'Start' in enhanced_results.columns and 'End' in enhanced_results.columns:
            enhanced_results['Start'] = pd.to_datetime(enhanced_results['Start'])
            enhanced_results['End'] = pd.to_datetime(enhanced_results['End'])
            
            # 计算交易天数
            enhanced_results['交易天数'] = (enhanced_results['End'] - enhanced_results['Start']).dt.days
            
            # 计算年化收益率
            enhanced_results['年化收益率 [%]'] = enhanced_results['Return [%]'] * (365 / enhanced_results['交易天数'])
            
        return enhanced_results
    
    def generate_performance_summary(self, results, title="策略性能汇总"):
        """
        生成性能汇总表格
        
        Parameters:
            results (pd.DataFrame): 回测结果数据
            title (str): 表格标题
            
        Returns:
            pd.DataFrame: 性能汇总表格
        """
        # 计算额外指标
        enhanced_results = self.calculate_metrics(results)
        
        # 选择要显示的指标
        metrics = [
            'Return [%]', 
            '年化收益率 [%]',
            'Max. Drawdown [%]', 
            '风险调整后收益',
            'Sharpe Ratio', 
            '# Trades', 
            'Win Rate [%]',
            '平均每笔交易收益',
            '交易天数'
        ]
        
        # 筛选存在的指标
        available_metrics = [m for m in metrics if m in enhanced_results.columns]
        
        # 创建汇总表格
        summary = enhanced_results[available_metrics].copy()
        
        # 添加表格标题
        summary.columns.name = title
        
        return summary
    
    def plot_performance_comparison(self, results_dict, metric='Return [%]', title=None):
        """
        绘制不同策略或股票的性能比较图
        
        Parameters:
            results_dict (dict): 策略名称到回测结果的映射
            metric (str): 要比较的指标
            title (str, optional): 图表标题
            
        Returns:
            matplotlib.figure.Figure: 生成的图表
        """
        if not title:
            title = f"不同策略的{metric}比较"
            
        # 提取要比较的数据
        comparison_data = {}
        
        for strategy_name, symbols_data in results_dict.items():
            for symbol, data in symbols_data.items():
                if metric in data.columns:
                    key = f"{strategy_name}_{symbol}"
                    comparison_data[key] = data[metric].values[0]
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 绘制条形图
        bars = ax.bar(comparison_data.keys(), comparison_data.values())
        
        # 设置图表标题和标签
        ax.set_title(title, fontsize=16)
        ax.set_xlabel('策略_股票', fontsize=12)
        ax.set_ylabel(metric, fontsize=12)
        
        # 旋转x轴标签以避免重叠
        plt.xticks(rotation=45, ha='right')
        
        # 在每个条形上显示数值
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        
        return fig
    
    def plot_trade_analysis(self, trades_data, title="交易分析"):
        """
        绘制交易分析图表
        
        Parameters:
            trades_data (pd.DataFrame): 交易数据，包含买入卖出时间和价格
            title (str): 图表标题
            
        Returns:
            matplotlib.figure.Figure: 生成的图表
        """
        # 创建图表
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 绘制价格线
        ax.plot(trades_data['日期'], trades_data['价格'], label='价格', color='gray', alpha=0.6)
        
        # 绘制买入点
        buy_points = trades_data[trades_data['操作'] == '买入']
        ax.scatter(buy_points['日期'], buy_points['价格'], color='green', s=100, label='买入', marker='^')
        
        # 绘制卖出点
        sell_points = trades_data[trades_data['操作'] == '卖出']
        ax.scatter(sell_points['日期'], sell_points['价格'], color='red', s=100, label='卖出', marker='v')
        
        # 设置图表标题和标签
        ax.set_title(title, fontsize=16)
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('价格', fontsize=12)
        
        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=45)
        
        # 添加图例
        ax.legend()
        
        plt.tight_layout()
        
        return fig
    
    def plot_drawdown_analysis(self, equity_curve, title="回撤分析"):
        """
        绘制回撤分析图表
        
        Parameters:
            equity_curve (pd.DataFrame): 权益曲线数据
            title (str): 图表标题
            
        Returns:
            matplotlib.figure.Figure: 生成的图表
        """
        # 计算回撤
        peak = equity_curve.cummax()
        drawdown = (equity_curve - peak) / peak * 100
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # 绘制权益曲线
        ax1.plot(equity_curve.index, equity_curve, label='权益曲线')
        ax1.plot(peak.index, peak, label='峰值', linestyle='--', alpha=0.5)
        
        # 设置第一个子图的标题和标签
        ax1.set_title(title, fontsize=16)
        ax1.set_ylabel('权益', fontsize=12)
        ax1.legend()
        
        # 绘制回撤
        ax2.fill_between(drawdown.index, drawdown, 0, color='red', alpha=0.3)
        ax2.plot(drawdown.index, drawdown, color='red', label='回撤 %')
        
        # 设置第二个子图的标签
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylabel('回撤 (%)', fontsize=12)
        ax2.legend()
        
        # 格式化y轴为百分比
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0f}%'))
        
        plt.tight_layout()
        
        return fig
    
    def generate_monthly_returns_heatmap(self, returns_data, title="月度收益热图"):
        """
        生成月度收益热图
        
        Parameters:
            returns_data (pd.Series): 日收益率数据，索引为日期
            title (str): 图表标题
            
        Returns:
            matplotlib.figure.Figure: 生成的图表
        """
        # 确保索引是日期类型
        returns_data.index = pd.to_datetime(returns_data.index)
        
        # 计算月度收益
        monthly_returns = returns_data.resample('M').apply(lambda x: (1 + x).prod() - 1)
        
        # 创建月度收益表格
        monthly_returns_table = pd.DataFrame({
            'year': monthly_returns.index.year,
            'month': monthly_returns.index.month,
            'return': monthly_returns.values
        })
        
        # 透视表格以便于热图显示
        heatmap_data = monthly_returns_table.pivot_table(
            index='year', 
            columns='month', 
            values='return'
        )
        
        # 设置月份名称
        month_names = ['一月', '二月', '三月', '四月', '五月', '六月', 
                       '七月', '八月', '九月', '十月', '十一月', '十二月']
        heatmap_data.columns = month_names[:len(heatmap_data.columns)]
        
        # 创建热图
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 绘制热图
        sns.heatmap(
            heatmap_data * 100,  # 转换为百分比
            annot=True,
            fmt='.2f',
            cmap='RdYlGn',
            center=0,
            linewidths=1,
            cbar_kws={'label': '收益率 (%)'},
            ax=ax
        )
        
        # 设置标题和标签
        ax.set_title(title, fontsize=16)
        ax.set_ylabel('年份', fontsize=12)
        
        plt.tight_layout()
        
        return fig
    
    def generate_nasdaq100_analysis_report(self, analysis_file_path, output_dir=None):
        """
        生成纳斯达克100指数成分股分析报表
        
        Parameters:
            analysis_file_path (str): 分析数据CSV文件路径
            output_dir (str, optional): 报表输出目录，如果为None则使用默认目录
            
        Returns:
            str: 报告HTML文件路径
        """
        if output_dir is None:
            output_dir = self.output_dir
            
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载分析数据
        try:
            data = self.load_nasdaq100_analysis(analysis_file_path)
        except Exception as e:
            print(f"加载分析数据时出错: {str(e)}")
            return None
            
        # 获取最新日期
        latest_date = data['Date'].max().strftime('%Y-%m-%d')
        
        # 计算汇总统计数据
        summary_stats = {
            '总股票数': len(data['Symbol'].unique()),
            '买入信号股票数': len(data[data['Buy Signal'] == 'Yes']),
            '卖出信号股票数': len(data[data['Sell Signal'] == 'Yes']),
            '上升趋势股票数': len(data[data['In Uptrend'] == 'Yes']),
            '平均收益率': data['Return [%]'].mean(),
            '最高收益率': data['Return [%]'].max(),
            '最低收益率': data['Return [%]'].min()
        }
        
        # 生成买入信号股票列表
        buy_signals = data[data['Buy Signal'] == 'Yes'].sort_values('Return [%]', ascending=False)
        
        # 生成卖出信号股票列表
        sell_signals = data[data['Sell Signal'] == 'Yes'].sort_values('Return [%]', ascending=False)
        
        # 生成表现最好的股票列表（按收益率排序）
        top_performers = data.sort_values('Return [%]', ascending=False).head(10)
        
        # 生成表现最差的股票列表（按收益率排序）
        bottom_performers = data.sort_values('Return [%]', ascending=True).head(10)
        
        # 生成HTML表格
        def generate_html_table(df, columns=None):
            if columns is None:
                columns = df.columns
                
            html = "<table border='1' cellpadding='5' cellspacing='0' style='width:100%;'>\n"
            
            # 添加表头
            html += "  <tr>\n"
            for col in columns:
                html += f"    <th>{col}</th>\n"
            html += "  </tr>\n"
            
            # 添加数据行
            for _, row in df.iterrows():
                html += "  <tr>\n"
                for col in columns:
                    value = row[col]
                    if isinstance(value, (int, float)) and col == 'Return [%]':
                        html += f"    <td>{value:.2f}%</td>\n"
                    else:
                        html += f"    <td>{value}</td>\n"
                html += "  </tr>\n"
            
            html += "</table>"
            return html
            
        # 生成报告HTML
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>纳斯达克100指数成分股分析报表 - {latest_date}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .metric-card {{ 
                    display: inline-block; 
                    width: 200px; 
                    margin: 10px; 
                    padding: 15px; 
                    border-radius: 5px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
                    text-align: center;
                }}
                .metric-value {{ 
                    font-size: 24px; 
                    font-weight: bold; 
                    margin: 10px 0; 
                }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .chart-container {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>纳斯达克100指数成分股分析报表</h1>
            <p>分析日期: {latest_date}</p>
            
            <h2>市场概览</h2>
            <div class="metrics-container">
        """
        
        # 添加关键指标卡片
        for name, value in summary_stats.items():
            style = ""
            if name == '平均收益率' or name == '最高收益率' or name == '最低收益率':
                style = "positive" if value > 0 else "negative"
                value_str = f"{value:.2f}%"
            else:
                value_str = str(value)
                
            report_html += f"""
            <div class="metric-card">
                <h3>{name}</h3>
                <div class="metric-value {style}">{value_str}</div>
            </div>
            """
            
        report_html += """
            </div>
            
            <h2>买入信号股票</h2>
        """
        
        if len(buy_signals) > 0:
            report_html += generate_html_table(buy_signals, ['Symbol', 'Name', 'Price', 'Return [%]', 'In Uptrend', 'Notes'])
        else:
            report_html += "<p>当前没有买入信号的股票</p>"
            
        report_html += """
            <h2>卖出信号股票</h2>
        """
        
        if len(sell_signals) > 0:
            report_html += generate_html_table(sell_signals, ['Symbol', 'Name', 'Price', 'Return [%]', 'In Uptrend', 'Notes'])
        else:
            report_html += "<p>当前没有卖出信号的股票</p>"
            
        report_html += """
            <h2>表现最好的10只股票</h2>
        """
        
        report_html += generate_html_table(top_performers, ['Symbol', 'Name', 'Price', 'Return [%]', 'Buy Signal', 'Sell Signal', 'In Uptrend'])
        
        report_html += """
            <h2>表现最差的10只股票</h2>
        """
        
        report_html += generate_html_table(bottom_performers, ['Symbol', 'Name', 'Price', 'Return [%]', 'Buy Signal', 'Sell Signal', 'In Uptrend'])
        
        report_html += """
            <h2>分析结论</h2>
            <p>
                基于以上数据，我们可以得出以下结论：
            </p>
            <ul>
        """
        
        # 添加分析结论
        avg_return = summary_stats['平均收益率']
        buy_signal_count = summary_stats['买入信号股票数']
        sell_signal_count = summary_stats['卖出信号股票数']
        uptrend_count = summary_stats['上升趋势股票数']
        total_stocks = summary_stats['总股票数']
        
        if avg_return > 0:
            report_html += f"<li>纳斯达克100指数成分股的平均收益率为 {avg_return:.2f}%，整体表现良好。</li>"
        else:
            report_html += f"<li>纳斯达克100指数成分股的平均收益率为 {avg_return:.2f}%，整体表现不佳。</li>"
            
        if buy_signal_count > 0:
            buy_pct = (buy_signal_count / total_stocks) * 100
            report_html += f"<li>有 {buy_signal_count} 只股票（占比 {buy_pct:.2f}%）显示买入信号，可考虑适当布局。</li>"
        else:
            report_html += "<li>当前没有股票显示买入信号，建议观望等待机会。</li>"
            
        if sell_signal_count > 0:
            sell_pct = (sell_signal_count / total_stocks) * 100
            report_html += f"<li>有 {sell_signal_count} 只股票（占比 {sell_pct:.2f}%）显示卖出信号，注意控制风险。</li>"
        
        uptrend_pct = (uptrend_count / total_stocks) * 100
        report_html += f"<li>有 {uptrend_count} 只股票（占比 {uptrend_pct:.2f}%）处于上升趋势中。</li>"
        
        if uptrend_pct > 50:
            report_html += "<li>大部分股票处于上升趋势，市场整体向好。</li>"
        else:
            report_html += "<li>大部分股票不处于上升趋势，市场可能面临调整。</li>"
            
        report_html += """
            </ul>
            
            <h2>投资建议</h2>
            <p>
                基于以上分析，我们提出以下投资建议：
            </p>
            <ul>
        """
        
        # 添加投资建议
        if buy_signal_count > sell_signal_count and uptrend_count > total_stocks / 2:
            report_html += "<li>市场整体向好，可适当增加仓位，重点关注有买入信号且处于上升趋势的股票。</li>"
        elif buy_signal_count < sell_signal_count and uptrend_count < total_stocks / 2:
            report_html += "<li>市场整体走弱，建议降低仓位，规避风险。</li>"
        else:
            report_html += "<li>市场信号混杂，建议保持中性仓位，选择性布局强势股。</li>"
            
        if len(top_performers) > 0:
            top_symbols = ", ".join(top_performers['Symbol'].head(3).tolist())
            report_html += f"<li>表现最好的股票（{top_symbols}等）可能存在短期获利回吐压力，建议适当关注。</li>"
            
        if len(bottom_performers) > 0:
            bottom_symbols = ", ".join(bottom_performers['Symbol'].head(3).tolist())
            report_html += f"<li>表现最差的股票（{bottom_symbols}等）可能存在超跌反弹机会，但需注意基本面风险。</li>"
            
        report_html += """
            </ul>
        </body>
        </html>
        """
        
        # 保存报告
        report_filename = f"nasdaq100_analysis_{latest_date.replace('-', '')}.html"
        report_path = os.path.join(output_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
            
        print(f"纳斯达克100指数成分股分析报表已生成并保存到: {report_path}")
        
        return report_path
    
    def generate_full_report(self, strategy_name, symbol, start_date=None, end_date=None):
        """
        生成完整的策略分析报告
        
        Parameters:
            strategy_name (str): 策略名称
            symbol (str): 股票代码
            start_date (str, optional): 开始日期
            end_date (str, optional): 结束日期
            
        Returns:
            str: 报告HTML内容
        """
        # 构建文件名
        file_name = f"{strategy_name}_{symbol}_results.csv"
        file_path = os.path.join(self.results_dir, file_name)
        
        # 加载回测结果
        results = self.load_results(file_path)
        
        # 计算额外指标
        enhanced_results = self.calculate_metrics(results)
        
        # 生成报告HTML
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{strategy_name} 策略分析报告 - {symbol}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .metric-card {{ 
                    display: inline-block; 
                    width: 200px; 
                    margin: 10px; 
                    padding: 15px; 
                    border-radius: 5px; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
                    text-align: center;
                }}
                .metric-value {{ 
                    font-size: 24px; 
                    font-weight: bold; 
                    margin: 10px 0; 
                }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .chart-container {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>{strategy_name} 策略分析报告</h1>
            <p>股票代码: {symbol}</p>
            <p>分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>策略概述</h2>
            <div class="metrics-container">
        """
        
        # 添加关键指标卡片
        key_metrics = [
            ('总收益率', f"{enhanced_results['Return [%]'].values[0]:.2f}%", 
             'positive' if enhanced_results['Return [%]'].values[0] > 0 else 'negative'),
            ('最大回撤', f"{enhanced_results['Max. Drawdown [%]'].values[0]:.2f}%", 'negative'),
            ('夏普比率', f"{enhanced_results['Sharpe Ratio'].values[0]:.2f}", 
             'positive' if enhanced_results['Sharpe Ratio'].values[0] > 0 else 'negative'),
            ('交易次数', f"{enhanced_results['# Trades'].values[0]}", 'neutral'),
            ('胜率', f"{enhanced_results['Win Rate [%]'].values[0]:.2f}%", 
             'positive' if enhanced_results['Win Rate [%]'].values[0] > 50 else 'negative')
        ]
        
        for name, value, style in key_metrics:
            report_html += f"""
            <div class="metric-card">
                <h3>{name}</h3>
                <div class="metric-value {style}">{value}</div>
            </div>
            """
        
        # 添加完整的性能指标表格
        report_html += """
            </div>
            
            <h2>详细性能指标</h2>
            <table>
                <tr>
        """
        
        # 添加表头
        for col in enhanced_results.columns:
            report_html += f"<th>{col}</th>"
        
        report_html += """
                </tr>
                <tr>
        """
        
        # 添加数据行
        for i, value in enumerate(enhanced_results.iloc[0]):
            if isinstance(value, (int, float)):
                report_html += f"<td>{value:.4f}</td>"
            else:
                report_html += f"<td>{value}</td>"
        
        report_html += """
                </tr>
            </table>
            
            <h2>分析结论</h2>
            <p>
                基于回测结果，该策略的表现可以总结如下：
            </p>
            <ul>
        """
        
        # 添加分析结论
        if enhanced_results['Return [%]'].values[0] > 0:
            report_html += f"<li>策略在测试期间实现了 {enhanced_results['Return [%]'].values[0]:.2f}% 的正收益。</li>"
        else:
            report_html += f"<li>策略在测试期间产生了 {abs(enhanced_results['Return [%]'].values[0]):.2f}% 的亏损。</li>"
            
        report_html += f"<li>最大回撤为 {abs(enhanced_results['Max. Drawdown [%]'].values[0]):.2f}%，表明策略在市场下跌时的风险敞口。</li>"
        
        if enhanced_results['Sharpe Ratio'].values[0] > 1:
            report_html += "<li>夏普比率大于1，表明策略的风险调整后收益较好。</li>"
        else:
            report_html += "<li>夏普比率较低，表明策略的风险调整后收益不够理想。</li>"
            
        if enhanced_results['Win Rate [%]'].values[0] > 50:
            report_html += f"<li>胜率为 {enhanced_results['Win Rate [%]'].values[0]:.2f}%，高于50%，表明策略有较好的预测能力。</li>"
        else:
            report_html += f"<li>胜率为 {enhanced_results['Win Rate [%]'].values[0]:.2f}%，低于50%，表明策略的预测能力有待提高。</li>"
            
        report_html += f"<li>策略在测试期间共进行了 {enhanced_results['# Trades'].values[0]} 笔交易。</li>"
        
        # 结束HTML
        report_html += """
            </ul>
            
            <h2>建议</h2>
            <p>
                基于以上分析，我们提出以下建议：
            </p>
            <ul>
                <li>考虑调整策略参数以提高胜率和降低最大回撤。</li>
                <li>在实盘交易前，建议进行更多的历史数据回测和前向测试。</li>
                <li>考虑将该策略与其他策略组合，以分散风险并提高整体表现。</li>
            </ul>
        </body>
        </html>
        """
        
        # 保存报告
        report_path = os.path.join(self.output_dir, f"{strategy_name}_{symbol}_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
            
        print(f"报告已生成并保存到: {report_path}")
        
        return report_html
    
    def batch_generate_reports(self, strategy_types=None):
        """
        批量生成多个策略的分析报告
        
        Parameters:
            strategy_types (list, optional): 要生成报告的策略类型列表
            
        Returns:
            dict: 生成的报告路径映射
        """
        # 获取所有结果文件
        all_files = os.listdir(self.results_dir)
        csv_files = [f for f in all_files if f.endswith('.csv')]
        
        # 筛选策略类型
        if strategy_types:
            csv_files = [f for f in csv_files if any(f.startswith(st) for st in strategy_types)]
            
        # 生成报告
        report_paths = {}
        
        for file in csv_files:
            parts = file.split('_')
            if len(parts) >= 2:
                strategy_name = parts[0]
                symbol = parts[1]
                
                try:
                    self.generate_full_report(strategy_name, symbol)
                    report_path = os.path.join(self.output_dir, f"{strategy_name}_{symbol}_report.html")
                    
                    if strategy_name not in report_paths:
                        report_paths[strategy_name] = {}
                        
                    report_paths[strategy_name][symbol] = report_path
                    
                except Exception as e:
                    print(f"生成 {strategy_name} - {symbol} 报告时出错: {str(e)}")
                    
        return report_paths


def analyze_strategy_results(strategy_name, symbol, results_dir='data/csv', output_dir='reports'):
    """
    分析策略回测结果并生成报告
    
    Parameters:
        strategy_name (str): 策略名称
        symbol (str): 股票代码
        results_dir (str): 回测结果CSV文件所在目录
        output_dir (str): 报表输出目录
        
    Returns:
        str: 报告文件路径
    """
    # 创建报表生成器
    generator = ReportGenerator(results_dir, output_dir)
    
    # 生成报告
    generator.generate_full_report(strategy_name, symbol)
    
    # 返回报告路径
    return os.path.join(output_dir, f"{strategy_name}_{symbol}_report.html")


def compare_strategies(strategy_names, symbol, metric='Return [%]', results_dir='data/csv', output_dir='reports'):
    """
    比较多个策略的性能并生成对比报告
    
    Parameters:
        strategy_names (list): 策略名称列表
        symbol (str): 股票代码
        metric (str): 要比较的指标
        results_dir (str): 回测结果CSV文件所在目录
        output_dir (str): 报表输出目录
        
    Returns:
        str: 报告文件路径
    """
    # 创建报表生成器
    generator = ReportGenerator(results_dir, output_dir)
    
    # 加载各个策略的结果
    results = {}
    
    for strategy in strategy_names:
        file_path = os.path.join(results_dir, f"{strategy}_{symbol}_results.csv")
        
        if os.path.exists(file_path):
            if strategy not in results:
                results[strategy] = {}
                
            results[strategy][symbol] = generator.load_results(file_path)
    
    # 生成比较图表
    if results:
        fig = generator.plot_performance_comparison(
            results, 
            metric=metric,
            title=f"{symbol} 不同策略的 {metric} 比较"
        )
        
        # 保存图表
        comparison_path = os.path.join(output_dir, f"strategy_comparison_{symbol}_{metric}.png")
        fig.savefig(comparison_path)
        plt.close(fig)
        
        print(f"策略比较图表已保存到: {comparison_path}")
        return comparison_path
    
    return None


def batch_analyze_all_results(results_dir='data/csv', output_dir='reports'):
    """
    批量分析所有回测结果并生成报告
    
    Parameters:
        results_dir (str): 回测结果CSV文件所在目录
        output_dir (str): 报表输出目录
        
    Returns:
        dict: 生成的报告路径映射
    """
    # 创建报表生成器
    generator = ReportGenerator(results_dir, output_dir)
    
    # 批量生成报告
    return generator.batch_generate_reports()


def analyze_nasdaq100_data(analysis_file_path, output_dir='reports'):
    """
    分析纳斯达克100指数成分股数据并生成报表
    
    Parameters:
        analysis_file_path (str): 分析数据CSV文件路径
        output_dir (str): 报表输出目录
        
    Returns:
        str: 报告文件路径
    """
    # 创建报表生成器
    generator = ReportGenerator(output_dir=output_dir)
    
    # 生成报告
    return generator.generate_nasdaq100_analysis_report(analysis_file_path, output_dir)


if __name__ == "__main__":
    # 示例用法
    # 分析单个策略
    # analyze_strategy_results('dual_ma', 'AAPL')
    
    # 比较多个策略
    # compare_strategies(['dual_ma', 'macd'], 'AAPL')
    
    # 批量分析所有结果
    # batch_analyze_all_results()
    
    # 分析纳斯达克100指数成分股数据
    analyze_nasdaq100_data('data/analysis/nasdaq100_analysis.csv')
