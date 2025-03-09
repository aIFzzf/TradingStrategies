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
│   └── multi_timeframe_strategy.py # 多周期策略
├── common/               # 公共工具模块
│   ├── __init__.py          # 模块初始化文件
│   └── timeframe_utils.py   # 时间周期转换工具
├── backtest_engine.py       # 回测引擎
├── run_strategy.py          # 运行策略的命令行工具
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
from strategies import DualMAStrategy, MACrossRSI, BollingerBandStrategy, MACDStrategy, MultiTimeframeStrategy, MultiTFStrategy
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

# 显示结果
print(stats1)
bt1.plot()
```

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

### 时间周期转换工具

`common.timeframe_utils`模块提供了以下功能：

- **resample_to_weekly**: 将日线数据重采样为周线数据
- **resample_to_monthly**: 将日线数据重采样为月线数据
- **resample_to_timeframe**: 将数据重采样为指定的时间周期
- **map_higher_timeframe_to_daily**: 将高周期数据映射到日线数据
- **calculate_ma**: 计算移动平均线
- **get_timeframe_data**: 获取指定时间周期的数据
- **align_timeframes**: 将不同周期的数据对齐到日线时间轴

使用示例：

```python
from common.timeframe_utils import resample_to_weekly, calculate_ma, align_timeframes

# 获取日线数据
daily_data = get_stock_data('AAPL', '2020-01-01', '2023-12-31')

# 转换为周线数据
weekly_data = resample_to_weekly(daily_data)

# 计算不同周期的均线
daily_ma = calculate_ma(daily_data, 20)
weekly_ma = calculate_ma(weekly_data, 10)

# 将不同周期的数据对齐到日线时间轴
aligned_data = align_timeframes(daily_data, weekly_data=weekly_data)
```

## 如何使用多周期工具

本项目提供了强大的多周期工具，可以帮助您在策略中结合不同时间周期的数据进行交易决策。以下是一些使用示例：

### 1. 在策略中使用多周期数据

```python
from common.timeframe_utils import resample_to_weekly, resample_to_monthly, calculate_ma, map_higher_timeframe_to_daily

class MyMultiTimeframeStrategy(Strategy):
    def init(self):
        # 获取周线和月线数据
        self.weekly_data = resample_to_weekly(self.data.df.copy())
        self.monthly_data = resample_to_monthly(self.data.df.copy())
        
        # 计算不同周期的指标
        self.weekly_ma = calculate_ma(self.weekly_data, 10)
        self.monthly_ma = calculate_ma(self.monthly_data, 6)
        
        # 将高周期数据映射到日线时间轴
        self.weekly_ma_daily = self.I(map_higher_timeframe_to_daily, self.data.df, self.weekly_ma)
        self.monthly_ma_daily = self.I(map_higher_timeframe_to_daily, self.data.df, self.monthly_ma)
    
    def next(self):
        # 使用不同周期的指标进行交易决策
        if not self.position:
            # 月线趋势向上 + 周线金叉
            if (self.data.Close[-1] > self.monthly_ma_daily[-1] and 
                self.weekly_ma_daily[-1] > self.weekly_ma_daily[-2]):
                self.buy()
```

### 2. 在回测脚本中使用多周期数据

```python
from common.timeframe_utils import get_timeframe_data, align_timeframes

# 获取不同周期的数据
daily_data = get_stock_data('AAPL', '2020-01-01', '2023-12-31', interval='1d')
weekly_data = get_timeframe_data('AAPL', '2020-01-01', '2023-12-31', interval='1wk')
monthly_data = get_timeframe_data('AAPL', '2020-01-01', '2023-12-31', interval='1mo')

# 将不同周期的数据对齐到日线时间轴
aligned_data = align_timeframes(daily_data, 
                               weekly_data=weekly_data, 
                               monthly_data=monthly_data)

# 现在可以在日线时间轴上访问不同周期的数据
print(aligned_data['daily']['Close'])
print(aligned_data['weekly']['Close'])
print(aligned_data['monthly']['Close'])
```

### 3. 自定义周期转换

```python
from common.timeframe_utils import resample_to_timeframe

# 创建自定义周期的数据
biweekly_data = resample_to_timeframe(daily_data, '2W')  # 两周数据
quarterly_data = resample_to_timeframe(daily_data, 'Q')  # 季度数据
```

通过使用这些工具，您可以轻松地在策略中结合不同时间周期的数据，创建更加复杂和有效的交易策略。

## 策略说明

### 1. 双均线策略 (DualMAStrategy)

经典的双均线交叉策略：
- 当短期均线上穿长期均线时买入
- 当短期均线下穿长期均线时卖出
- 支持止损和止盈设置

参数：
- `fast_ma`: 短期均线周期
- `slow_ma`: 长期均线周期
- `stop_loss_pct`: 止损百分比
- `take_profit_pct`: 止盈百分比

### 2. 均线+RSI策略 (MACrossRSI)

结合均线和RSI指标的高级策略：
- 买入条件：短期均线上穿长期均线 AND RSI < 阈值(非超买)
- 卖出条件：短期均线下穿长期均线 OR RSI > 阈值(超买)
- 使用跟踪止损保护利润

参数：
- `fast_ma`: 短期均线周期
- `slow_ma`: 长期均线周期
- `rsi_period`: RSI计算周期
- `rsi_buy_threshold`: RSI买入阈值
- `rsi_sell_threshold`: RSI卖出阈值
- `trailing_sl_atr`: 跟踪止损的ATR倍数

### 3. 布林带策略 (BollingerBandStrategy)

基于布林带的交易策略：
- 买入条件：价格触及布林带下轨
- 卖出条件：价格触及布林带上轨
- 支持止损设置

参数：
- `bb_period`: 布林带计算周期
- `bb_std`: 布林带标准差倍数
- `stop_loss_pct`: 止损百分比

### 4. MACD策略 (MACDStrategy)

基于MACD指标的交易策略：
- 买入条件：MACD线上穿信号线（金叉）
- 卖出条件：MACD线下穿信号线（死叉）
- 支持止损和止盈设置

参数：
- `fast_period`: MACD快线周期
- `slow_period`: MACD慢线周期
- `signal_period`: MACD信号线周期
- `stop_loss_pct`: 止损百分比
- `take_profit_pct`: 止盈百分比

### 5. 多周期策略 (MultiTimeframeStrategy)

多周期策略结合了周线和月线数据进行交易决策：

- **月线**：确定大趋势方向（价格在月线均线之上为上升趋势）
- **周线**：寻找入场点（短期均线上穿长期均线为买入信号）

参数：
- `weekly_fast_ma`: 周线短期均线周期
- `weekly_slow_ma`: 周线长期均线周期
- `monthly_ma`: 月线均线周期
- `stop_loss_pct`: 止损百分比
- `take_profit_pct`: 止盈百分比

**注意**：多周期策略需要使用日线数据作为输入，策略内部会自动将其转换为周线和月线数据。策略使用了`common.timeframe_utils`模块中的工具函数进行时间周期转换。

### 6. 多周期组合策略 (MultiTFStrategy)

多周期组合策略结合了短期和长期均线进行交易决策：

- **短期均线**：寻找入场点（短期均线上穿长期均线为买入信号）
- **长期均线**：确定大趋势方向（价格在长期均线之上为上升趋势）

参数：
- `short_ma`: 短期均线周期
- `long_ma`: 长期均线周期
- `signal_ma`: 信号线周期
- `stop_loss_pct`: 止损百分比
- `take_profit_pct`: 止盈百分比

**注意**：多周期策略需要使用日线数据作为输入，策略内部会自动将其转换为周线和月线数据。

## 扩展策略

要添加新的策略，请按照以下步骤操作：

1. 在 `strategies` 目录下创建新的策略文件，例如 `my_strategy.py`
2. 实现策略类，继承自 `Strategy` 或其他基类
3. 在 `strategies/__init__.py` 中导入并导出新策略
4. 在 `run_strategy.py` 中添加相应的命令行选项和处理逻辑

示例：
```python
# strategies/my_strategy.py
from backtesting import Strategy

class MyStrategy(Strategy):
    # 实现策略逻辑
    ...

# strategies/__init__.py
from .my_strategy import MyStrategy
__all__ = ['DualMAStrategy', 'MACrossRSI', 'BollingerBandStrategy', 'MACDStrategy', 'MultiTimeframeStrategy', 'MultiTFStrategy', 'MyStrategy']

```

## 回测结果解释

回测完成后，将显示以下主要指标：

- **Return [%]**: 总回报率
- **Buy & Hold Return [%]**: 买入持有策略的回报率
- **Max. Drawdown [%]**: 最大回撤百分比
- **# Trades**: 交易次数
- **Win Rate [%]**: 盈利交易的百分比
- **Sharpe Ratio**: 夏普比率，衡量风险调整后的回报
- **Sortino Ratio**: 索提诺比率，只考虑下行风险
- **Calmar Ratio**: 卡玛比率，回报与最大回撤的比值

## 注意事项

- 过去的表现不代表未来的结果
- 回测结果可能受到过拟合的影响
- 实际交易中还需考虑滑点、流动性等因素
- 建议在实盘交易前进行充分的测试和风险评估
