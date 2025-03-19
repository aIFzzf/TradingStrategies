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
├── scripts/              # 脚本目录
│   ├── analysis/            # 分析脚本
│       ├── get_nasdaq_top100.py  # 获取纳斯达克前100股票
│       └── batch_analyze_stocks.py # 批量分析股票
├── .github/              # GitHub相关配置
│   └── workflows/           # GitHub Actions工作流
│       └── analyze_stocks.yml  # 自动分析股票工作流
├── backtest_engine.py       # 回测引擎
├── run_strategy.py          # 运行策略的命令行工具
├── run_long_term_strategy.py # 运行长期MACD策略
├── run_interactive_chart.py # 运行交互式图表
├── custom_data_example.py   # 使用自定义数据的示例
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

### GitHub自动化流水线

本项目配置了GitHub Actions工作流，可以自动化运行股票分析：

1. 每周一自动运行（也可以手动触发）
2. 获取纳斯达克前100股票
3. 运行策略分析
4. 保存分析结果
5. 将结果提交回仓库

工作流配置文件位于`.github/workflows/analyze_stocks.yml`。

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
3. **数据同步**：注意不同周期数据的日期对齐问题
4. **避免过度拟合**：增加周期虽然可以提供更多信息，但也增加了过度拟合的风险

## 数据周期选项

本框架支持使用不同的时间周期进行回测：

- **日线数据 (1d)**: 默认选项，适合短期到中期的交易策略
- **周线数据 (1wk)**: 适合中期交易策略，减少噪音
- **月线数据 (1mo)**: 适合长期投资策略，关注大趋势

可以通过两种方式获取不同周期的数据：

1. **直接获取**: 使用`get_stock_data`函数的`interval`参数
   ```python
   # 获取周线数据
   weekly_data = get_stock_data('AAPL', '2018-01-01', '2023-12-31', interval='1wk')
   ```

2. **重采样**: 使用公共工具模块中的函数对已有的日线数据进行重采样
   ```python
   from common.timeframe_utils import resample_to_weekly, resample_to_monthly, resample_to_timeframe
   
   # 将日线数据重采样为周线
   weekly_data = resample_to_weekly(daily_data)
   
   # 将日线数据重采样为月线
   monthly_data = resample_to_monthly(daily_data)
   
   # 使用通用函数重采样为任意周期
   weekly_data = resample_to_timeframe(daily_data, 'W')  # 周线
   monthly_data = resample_to_timeframe(daily_data, 'M')  # 月线
   quarterly_data = resample_to_timeframe(daily_data, 'Q')  # 季线
   yearly_data = resample_to_timeframe(daily_data, 'Y')  # 年线
   ```

在命令行中，使用`--interval`参数指定数据周期：
```bash
# 使用周线数据运行策略
python run_strategy.py --symbol AAPL --interval 1wk --strategy dual_ma
```

## 公共工具模块

项目包含一个`common`模块，提供了各种可复用的工具函数：

### 技术指标计算 (indicators.py)

```python
from common.indicators import SMA, EMA, RSI, MACD, BollingerBands, ATR, STOCH

# 计算简单移动平均线
sma = SMA(daily_data, 20)

# 计算指数移动平均线
ema = EMA(daily_data, 20)

# 计算相对强弱指数
rsi = RSI(daily_data, 14)

# 计算MACD指标
dif, dea, macd = MACD(daily_data, 12, 26, 9)

# 计算布林带
upper, middle, lower = BollingerBands(daily_data, 20, 2)

# 计算真实波动幅度均值
atr = ATR(daily_data, 14)

# 计算随机指标(KD)
stoch = STOCH(daily_data, 14, 3, 3)
```

### 时间周期转换 (timeframe_utils.py)

```python
from common.timeframe_utils import resample_to_weekly, resample_to_monthly, resample_to_timeframe, map_higher_timeframe_to_daily

# 将日线数据重采样为周线
weekly_data = resample_to_weekly(daily_data)

# 将日线数据重采样为月线
monthly_data = resample_to_monthly(daily_data)

# 使用通用函数重采样为任意周期
weekly_data = resample_to_timeframe(daily_data, 'W')  # 周线
monthly_data = resample_to_timeframe(daily_data, 'M')  # 月线
quarterly_data = resample_to_timeframe(daily_data, 'Q')  # 季线
yearly_data = resample_to_timeframe(daily_data, 'Y')  # 年线

# 将高周期数据映射回日线周期（用于在日线图表上显示高周期指标）
weekly_sma_daily = map_higher_timeframe_to_daily(weekly_sma, daily_data.index)
```

## 策略说明

### 1. 双均线策略 (DualMAStrategy)

双均线策略使用快速和慢速移动平均线的交叉点作为交易信号：

- 当快速均线上穿慢速均线时买入
- 当快速均线下穿慢速均线时卖出

```bash
python run_strategy.py --symbol AAPL --strategy dual_ma --fast_ma 10 --slow_ma 30
```

### 2. 均线+RSI策略 (MACrossRSI)

结合均线交叉和RSI指标的策略：

- 当快速均线上穿慢速均线且RSI>50时买入
- 当快速均线下穿慢速均线或RSI<30时卖出

```bash
python run_strategy.py --symbol MSFT --strategy ma_rsi --fast_ma 10 --slow_ma 30 --rsi_period 14
```

### 3. 布林带策略 (BollingerBandStrategy)

基于布林带的策略：

- 当价格突破下轨且RSI<30时买入
- 当价格突破上轨或RSI>70时卖出

```bash
python run_strategy.py --symbol GOOG --strategy bollinger --bb_period 20 --bb_std 2.0
```

### 4. MACD策略 (MACDStrategy)

基于MACD指标的策略：

- 当MACD金叉（DIF上穿DEA）时买入
- 当MACD死叉（DIF下穿DEA）时卖出

```bash
python run_strategy.py --symbol TSLA --strategy macd --fast_period 12 --slow_period 26 --signal_period 9
```

### 5. 长期MACD策略 (LongTermMACDStrategy)

使用月线、周线和日线的MACD指标进行多周期共振分析，寻找长期趋势的买卖点：

- 买入条件：
  1. 月线KDJ金叉
  2. 月线MACD DIF斜率向上
  3. 周线MACD金叉
  4. 日线K线向上突破EMA20均线或日线MACD金叉

- 卖出条件：
  1. 月线MACD值下降
  2. 周线MACD死叉且MACD值<0

```bash
python run_long_term_strategy.py --symbol AAPL --start 2018-01-01 --end 2023-12-31
```

**注意**：多周期策略需要使用日线数据作为输入，策略内部会自动将其转换为周线和月线数据。策略使用了`common.timeframe_utils`模块中的工具函数进行时间周期转换。

### 6. 多周期组合策略 (MultiTFStrategy)

多周期组合策略结合了短期和长期均线进行交易决策：

- 买入条件：
  1. 短期均线上穿长期均线
  2. 信号均线向上
  3. 价格位于长期均线之上

- 卖出条件：
  1. 短期均线下穿长期均线
  2. 信号均线向下
  3. 价格位于长期均线之下

```bash
python run_strategy.py --symbol AAPL --strategy multi_tf_strategy --short_ma 5 --long_ma 20 --signal_ma 10
```

## 自定义数据

除了使用Yahoo Finance的数据外，本框架还支持使用自定义数据源：

```python
# 加载自定义CSV数据
custom_data = pd.read_csv('my_stock_data.csv', index_col='Date', parse_dates=True)

# 确保数据包含必要的列：Open, High, Low, Close, Volume
required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
for col in required_columns:
    if col not in custom_data.columns:
        raise ValueError(f"自定义数据缺少必要的列: {col}")

# 运行回测
stats, bt = run_backtest(custom_data, DualMAStrategy)
```

示例代码见`custom_data_example.py`。

## 贡献指南

欢迎贡献新的策略或改进现有功能！请遵循以下步骤：

1. Fork本仓库
2. 创建新分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add some feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证。详情请参阅LICENSE文件。
