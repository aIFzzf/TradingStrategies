#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交易策略回测结果分析模块
"""

try:
    from .report_generator import (
        ReportGenerator,
        analyze_strategy_results,
        compare_strategies,
        batch_analyze_all_results
    )
except ImportError:
    # 如果完整版报表生成器导入失败，使用简化版
    print("警告: 完整版报表生成器导入失败，使用简化版报表生成器")
    from .simple_report import (
        generate_simple_report as analyze_strategy_results,
        compare_simple as compare_strategies
    )
    
    def batch_analyze_all_results(results_dir='data/csv', output_dir='reports'):
        """
        简化版批量分析函数
        """
        print("简化版批量分析功能暂不可用")
        return {}
