# THE ORACLE - Agent 1: Technical Analysis

MT5 Technical Analysis Agent for multi-timeframe market analysis.

## Features

### Timeframes Analyzed
- **D1** (Daily) - Primary trend direction
- **H4** (4-Hour) - Secondary trend
- **H1** (Hourly) - Trading timeframe
- **M15** (15-Minute) - Entry precision

### Indicators Calculated
- **Moving Averages**: MA 20, 50, 200
- **RSI**: 14-period with oversold/overbought detection
- **MACD**: 12/26/9 with histogram
- **Bollinger Bands**: 20-period, 2 std dev
- **ATR**: 14-period (volatility measure)
- **ADX**: 14-period with +DI/-DI (trend strength)

### Pattern Detection
- **Candlestick Patterns**: Doji, Hammer, Shooting Star, Engulfing, Morning/Evening Star
- **Chart Patterns**: Bull/Bear Flags, Price Channels (Ascending/Descending/Horizontal)
- **Support/Resistance**: Pivot-based levels with strength scoring

### Output
JSON structure with:
- Per-timeframe analysis (price, indicators, patterns, S/R levels)
- Overall bias (bullish/bearish/mixed)
- Confidence score (0-1)
- Alignment score (timeframe agreement)
- Key confluences detected
- Recommended direction (BUY/SELL/NEUTRAL)
- Invalidation level (stop loss reference)

## Usage

```bash
python agent_1_technical.py
```

Analyzes default symbols: EURUSD, GBPUSD, USDJPY

Output saved to: `../output/<SYMBOL>_<TIMESTAMP>_technical.json`

## Integration

Connects to MT5 via MetaTrader5 Python API. Requires MT5 terminal running.

```python
from agent_1_technical import TechnicalAnalyzer

analyzer = TechnicalAnalyzer()
analyzer.connect()
result = analyzer.analyze_symbol("EURUSD")
analyzer.save_analysis(result)
analyzer.disconnect()
```
