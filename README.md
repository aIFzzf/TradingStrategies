# 交易策略回测框架

本项目是一个基于 [backtesting.py](https://github.com/kernc/backtesting.py) 库的交易策略回测框架，提供了模块化的设计，使得策略开发和回测更加灵活和可维护。

## 项目结构

```
TradingStrategies/
├── strategies/           # 策略模块
│   ├── __init__.py          # 模块初始化文件
│   ├── dual_ma_strategy.py  # 双均线策略
│   ├── ma_rsi_strategy.py   # 均线+RSI策略
│   ├── bollinger_strategy.py # 布林带策略
│   ├── macd_strategy.py     # MACD策略
│   ├── multi_timeframe_strategy.py # 多周期策略
│   ├── long_term_macd_strategy.py # 长期MACD策略
│   ├── multi_tf_strategy.py # 多周期组合策略
│   └── ...
├── common/               # 公共工具模块
│   ├── __init__.py          # 模块初始化文件
│   ├── indicators.py        # 技术指标计算工具
│   └── timeframe_utils.py   # 时间周期转换工具
├── analysis/             # 分析和报表模块
│   ├── __init__.py          # 模块初始化文件
│   ├── report_generator.py  # 报表生成器
│   └── simple_report.py     # 简化版报表生成器
├── notification/         # 通知模块
│   ├── __init__.py          # 模块初始化文件
│   └── email_notification.py # 邮件通知功能
├── scripts/              # 脚本目录
│   ├── analysis/            # 分析脚本
│       ├── get_nasdaq_top100.py  # 获取纳斯达克前100股票
│       └── batch_analyze_stocks.py # 批量分析股票
├── .github/              # GitHub相关配置
│   └── workflows/           # GitHub Actions工作流
│       ├── analyze_stocks.yml  # 自动分析股票工作流
│       └── analyze_stocks_new.yml # 新版自动分析工作流（含报表生成和邮件通知）
├── reports/              # 报表输出目录
├── backtest_engine.py       # 回测引擎
├── run_strategy.py          # 运行策略的命令行工具
├── run_long_term_strategy.py # 运行长期MACD策略
├── run_interactive_chart.py # 运行交互式图表
├── custom_data_example.py   # 使用自定义数据的示例
├── .env.example             # 环境变量示例文件
└── README.md                # 项目说明文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行运行

```bash
# 运行双均线策略
python run_strategy.py --symbol AAPL --start 2020-01-01 --end 2023-12-31 --strategy dual_ma

# 运行均线+RSI策略
python run_strategy.py --symbol MSFT --start 2020-01-01 --end 2023-12-31 --strategy ma_rsi

# 运行布林带策略
python run_strategy.py --symbol GOOG --start 2020-01-01 --end 2023-12-31 --strategy bollinger

# 运行MACD策略
python run_strategy.py --symbol TSLA --start 2020-01-01 --end 2023-12-31 --strategy macd

# 运行多周期策略
python run_strategy.py --symbol AAPL --start 2020-01-01 --end 2023-12-31 --strategy multi_timeframe

# 运行多周期组合策略
python run_strategy.py --symbol AAPL --start 2020-01-01 --end 2023-12-31 --strategy multi_tf_strategy

# 运行长期MACD策略
python run_long_term_strategy.py --symbol AAPL --start 2018-01-01 --end 2023-12-31

# 使用不同的时间周期（周线、月线）
python run_strategy.py --symbol AAPL --start 2018-01-01 --end 2023-12-31 --strategy dual_ma --interval 1wk
python run_strategy.py --symbol MSFT --start 2015-01-01 --end 2023-12-31 --strategy macd --interval 1mo

# 优化策略参数
python run_strategy.py --symbol GOOG --start 2020-01-01 --end 2023-12-31 --strategy dual_ma --optimize

# 比较不同策略
python run_strategy.py --symbol AMZN --start 2020-01-01 --end 2023-12-31 --strategy compare

# 自定义参数
python run_strategy.py --symbol AAPL --start 2020-01-01 --end 2023-12-31 --strategy dual_ma --fast_ma 5 --slow_ma 20 --stop_loss 0.03 --take_profit 0.08

# 生成策略分析报表
python run_strategy.py --symbol AAPL --start 2020-01-01 --end 2023-12-31 --strategy dual_ma --generate_report

# 自动生成报表（在回测完成后自动生成相应的报表）
python run_strategy.py --symbol AAPL --start 2020-01-01 --end 2023-12-31 --strategy dual_ma --auto_report

# 发送邮件通知（需配置.env文件中的邮件设置）
python run_strategy.py --symbol AAPL --start 2020-01-01 --end 2023-12-31 --strategy dual_ma --auto_report --send_email

# 指定邮件接收者
python run_strategy.py --symbol AAPL --start 2020-01-01 --end 2023-12-31 --strategy dual_ma --auto_report --send_email --email_recipients "user@example.com"

# 运行指数分析（纳斯达克100）
python run_strategy.py --strategy index_analysis --index nasdaq100

# 运行指数分析（恒生科技50）
python run_strategy.py --strategy index_analysis --index hstech50

# 运行所有指数分析并发送邮件通知
python run_strategy.py --strategy index_analysis --index all --auto_report --send_email
```

### 在代码中使用

```python
from strategies import DualMAStrategy, MACrossRSI, BollingerBandStrategy, MACDStrategy, MultiTimeframeStrategy, MultiTFStrategy, LongTermMACDStrategy
from backtest_engine import get_stock_data, run_backtest, resample_data

# 获取数据
data = get_stock_data('AAPL', '2020-01-01', '2023-12-31')

# 获取周线数据
weekly_data = get_stock_data('AAPL', '2018-01-01', '2023-12-31', interval='1wk')

# 获取月线数据
monthly_data = get_stock_data('AAPL', '2015-01-01', '2023-12-31', interval='1mo')

# 也可以对日线数据进行重采样
resampled_weekly = resample_data(data, interval='W')
resampled_monthly = resample_data(data, interval='M')

# 运行双均线策略回测（使用日线数据）
stats1, bt1 = run_backtest(data, DualMAStrategy, fast_ma=10, slow_ma=30)

# 运行布林带策略回测（使用周线数据）
stats2, bt2 = run_backtest(weekly_data, BollingerBandStrategy, bb_period=20, bb_std=2.0)

# 运行MACD策略回测（使用月线数据）
stats3, bt3 = run_backtest(monthly_data, MACDStrategy, fast_period=12, slow_period=26, signal_period=9)

# 运行多周期策略回测（使用日线数据）
stats4, bt4 = run_backtest(data, MultiTimeframeStrategy, weekly_fast_ma=10, weekly_slow_ma=30, monthly_ma=60)

# 运行多周期组合策略回测（使用日线数据）
stats5, bt5 = run_backtest(data, MultiTFStrategy, short_ma=5, long_ma=20, signal_ma=10)

# 运行长期MACD策略回测（使用日线数据）
stats6, bt6 = run_backtest(data, LongTermMACDStrategy, fast_period=12, slow_period=26, signal_period=9)

# 显示结果
print(stats1)
bt1.plot()
```

## 批量分析股票

本项目提供了批量分析股票的功能，可以自动获取纳斯达克前100的股票并应用交易策略进行分析。

### 获取纳斯达克前100股票

```bash
python scripts/analysis/get_nasdaq_top100.py
```

这将获取纳斯达克100指数的成分股列表，并保存到`nasdaq100_symbols.json`文件中。

### 批量分析股票

```bash
# 分析所有股票
python scripts/analysis/batch_analyze_stocks.py --output nasdaq100_analysis.csv

# 只输出有买入信号的股票
python scripts/analysis/batch_analyze_stocks.py --signal_only --output nasdaq100_analysis.csv

# 自定义参数
python scripts/analysis/batch_analyze_stocks.py --start 2018-01-01 --end 2023-12-31 --max_workers 10 --signal_only
```

## 报表生成功能

本项目提供了多种报表生成功能，可以生成HTML格式的分析报表，方便查看和分享。

### 策略回测报表

```bash
# 生成策略回测报表
python run_strategy.py --symbol AAPL --strategy dual_ma --generate_report

# 自动生成报表（在回测完成后自动生成）
python run_strategy.py --symbol AAPL --strategy dual_ma --auto_report
```

### 指数分析报表

```bash
# 生成纳斯达克100指数分析报表
python run_strategy.py --strategy index_analysis --index nasdaq100

# 生成恒生科技50指数分析报表
python run_strategy.py --strategy index_analysis --index hstech50

# 生成所有指数分析报表
python run_strategy.py --strategy index_analysis --index all
```

### 策略比较报表

```bash
# 生成策略比较报表
python run_strategy.py --symbol AAPL --strategy compare --compare_report
```

### 使用simple_report.py直接生成报表

```bash
# 生成策略回测报表
python analysis/simple_report.py strategy --strategy_name dual_ma --symbol AAPL

# 生成纳斯达克100指数分析报表
python analysis/simple_report.py nasdaq100

# 生成恒生科技50指数分析报表
python analysis/simple_report.py hstech50

# 比较多个策略
python analysis/simple_report.py compare --strategy_names dual_ma,macd,bollinger --symbol AAPL
```

## 邮件通知功能

本项目支持通过邮件发送分析报表，方便及时获取分析结果。

### 配置邮件设置

在项目根目录创建`.env`文件（参考`.env.example`），配置以下环境变量：

```
EMAIL_SENDER=your_email@example.com
EMAIL_PASSWORD=your_email_password_or_app_password
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
```

### 发送邮件通知

```bash
# 运行策略并发送邮件通知
python run_strategy.py --symbol AAPL --strategy dual_ma --auto_report --send_email

# 指定邮件接收者
python run_strategy.py --symbol AAPL --strategy dual_ma --auto_report --send_email --email_recipients "user@example.com"

# 运行指数分析并发送邮件通知
python run_strategy.py --strategy index_analysis --index all --auto_report --send_email
```

### 在代码中使用邮件通知

```python
from notification import EmailNotifier, send_email_notification

# 方法1：使用EmailNotifier类
notifier = EmailNotifier()
notifier.send_email(
    to_emails=["user@example.com"],
    subject="策略分析报告",
    body="请查看附件中的策略分析报告",
    attachments=["reports/strategy_report.html"]
)

# 方法2：使用便捷函数
send_email_notification(
    to_emails=["user@example.com"],
    subject="策略分析报告",
    body="请查看附件中的策略分析报告",
    attachments=["reports/strategy_report.html"]
)
```

## GitHub自动化流水线

本项目配置了GitHub Actions工作流，可以自动化运行股票分析：

1. 每周一自动运行（也可以手动触发）
2. 获取纳斯达克前100股票和恒生科技50指数成分股
3. 运行策略分析
4. 生成分析报表
5. 发送邮件通知
6. 将结果提交回仓库

工作流配置文件位于`.github/workflows/analyze_stocks_new.yml`。

## 多周期组合策略

本框架支持使用多个不同周期的数据进行组合分析和交易决策。多周期策略的主要优势：

1. **减少假信号**：通过结合不同周期的指标，可以过滤掉短期市场噪音
2. **捕捉大趋势**：使用长周期（如月线）确定市场大方向
3. **精确入场**：使用短周期（如日线或周线）寻找最佳入场点

### 多周期策略的实现方式

在我们的框架中，有两种方式实现多周期策略：

1. **使用内置的多周期策略**：
   ```bash
   # 运行内置的多周期策略（结合周线和月线）
   python run_strategy.py --symbol AAPL --strategy multi_tf_strategy
   ```

2. **自定义多周期组合**：
   ```python
   # 获取不同周期的数据
   daily_data = get_stock_data('AAPL', '2020-01-01', '2023-12-31', interval='1d')
   weekly_data = get_stock_data('AAPL', '2020-01-01', '2023-12-31', interval='1wk')
   monthly_data = get_stock_data('AAPL', '2020-01-01', '2023-12-31', interval='1mo')
   
   # 分析不同周期的指标
   # 例如：月线判断趋势，周线寻找入场点
   monthly_trend = analyze_monthly_trend(monthly_data)
   weekly_signals = find_weekly_signals(weekly_data)
   
   # 根据多周期分析结果生成交易信号
   if monthly_trend == 'up' and weekly_signals == 'buy':
       # 执行买入操作
   ```

### 多周期策略开发建议

1. **先大后小原则**：先分析大周期确定趋势方向，再分析小周期寻找入场点
2. **周期协调**：确保不同周期之间的指标相互协调，避免相互矛盾
