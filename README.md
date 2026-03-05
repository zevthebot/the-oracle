# THE ORACLE
## AI-Powered Multi-Agent Forex Trading System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange.svg)]()

> **An intelligent trading system where AI has the final word.**

THE ORACLE combines multi-agent market analysis with the decision-making power of MiniMax M2.5 LLM to identify and execute high-probability forex trades.

---

## 🌟 Key Features

- **🧠 AI Brain**: MiniMax M2.5 LLM makes final trading decisions
- **📊 Multi-Agent Analysis**: Technical, News, and Sentiment agents gather market intelligence
- **⚡ Direct Execution**: No risk engine override - AI has full authority
- **🎯 Fresh Start Mode**: Each session starts independent (no daily loss limits)
- **📈 Live Trading**: Direct integration with MetaTrader 5

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      THE ORACLE v3.2                         │
├─────────────────────────────────────────────────────────────┤
│  Data Layer          │   AI Brain          │   Execution    │
│                      │                     │                │
│  ┌─────────────────┐ │  ┌───────────────┐ │  ┌──────────┐  │
│  │ Agent 1:        │ │  │               │ │  │          │  │
│  │ Technical       │ │  │  MiniMax      │ │  │   MT5    │  │
│  │ (D1/H4/H1/M15)  │─┤  │  M2.5 LLM     │─┤  │ Executor │  │
│  └─────────────────┘ │  │               │ │  └──────────┘  │
│  ┌─────────────────┐ │  └───────────────┘ │                │
│  │ Agent 2:        │ │        ↑           │                │
│  │ News &          │ │        │           │                │
│  │ Fundamentals    │─┘        │           │                │
│  └─────────────────┘          │           │                │
│  ┌─────────────────┐          │           │                │
│  │ Agent 3:        │          │           │                │
│  │ Sentiment       │──────────┘           │                │
│  │ Analysis        │                      │                │
│  └─────────────────┘                      │                │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | Purpose | Details |
|-----------|---------|---------|
| **Agent 1: Technical** | Price action analysis | Multi-timeframe trend detection, confluence scoring |
| **Agent 2: News** | Event awareness | Economic calendar, high-impact event detection |
| **Agent 3: Sentiment** | Market mood | USD strength index, risk-on/risk-off flows |
| **MiniMax LLM** | Decision engine | Analyzes all signals, decides trade/no-trade |
| **MT5 Executor** | Trade execution | Direct market orders with SL/TP |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- MetaTrader 5 (Windows)
- OpenRouter API key
- Pepperstone (or compatible) MT5 account

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/the-oracle.git
cd the-oracle

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENROUTER_API_KEY="your-api-key-here"

# Or create .env file
echo "OPENROUTER_API_KEY=your-api-key-here" > .env
```

### Running THE ORACLE

```bash
# Basic run with default settings
python the_oracle/orchestrator_kimi.py --balance 7733

# Custom symbols and balance
python the_oracle/orchestrator_kimi.py \
  --balance 10000 \
  --symbols EURUSD GBPUSD USDJPY AUDUSD
```

---

## 📊 How It Works

### 1. Market Intelligence Gathering

**Technical Agent** scans 4 timeframes (D1, H4, H1, M15):
```
EURUSD: SELL 37.5% (Sideways on D1, Bearish on H4)
GBPUSD: SELL 58.5% (Bearish alignment, strongest signal)
USDJPY: BUY 40.5% (Bullish on H4)
AUDUSD: SELL 37.5% (Mixed signals)
```

**News Agent** checks economic calendar:
```
High Impact Events: 1 (NFP in 2 hours)
Bias: high_volatility_expected
```

**Sentiment Agent** reads market mood:
```
USD Strength: 50.2/100 (Neutral)
Risk Tone: RISK_OFF
```

### 2. AI Analysis

All signals are sent to MiniMax M2.5:

```
Starting Balance: $7733
Session: NEW (fresh start)

Market Signals:
- GBPUSD: SELL 58.5% (strongest)
- USDJPY: BUY 40.5%
- EURUSD: SELL 37.5%
- AUDUSD: SELL 37.5%

USD: 50.2/100 | Risk: RISK_OFF
News: 1 event

DECISION?
```

### 3. LLM Decision

MiniMax responds with structured JSON:
```json
{
  "decision": "TRADE",
  "symbol": "GBPUSD",
  "direction": "SELL",
  "lot_size": 0.3,
  "confidence": 78,
  "reasoning": "GBPUSD shows strongest SELL signal at 58.5%. USD neutral with RISK_OFF environment favors dollar strength."
}
```

### 4. Execution

Trade executed immediately:
```
[TRADE] GBPUSD SELL
[INFO] Lot: 0.3, Confidence: 78%
[OK] EXECUTED: Ticket 59602307
Entry: 1.33176 | SL: 1.33676 | TP: 1.32426
```

---

## ⚙️ Configuration

### Fresh Start Mode

THE ORACLE operates in **Fresh Start Mode**:

- ❌ No daily loss tracking from previous sessions
- ❌ No cumulative win/loss affecting decisions  
- ✅ Balance provided = Starting capital for this session
- ✅ MiniMax evaluates each opportunity independently

### LLM Authority

MiniMax M2.5 has **full trading authority**:

- Chooses symbol, direction, and lot size
- Decides trade confidence threshold
- No risk engine override
- Direct execution on TRADE decision

### Safety Limits (Hard-coded)

```python
max_lot_size = 0.5
min_confidence = 75
sl_pips = 50
tp_pips = 75  # 1.5x SL
```

---

## 📁 Project Structure

```
the_oracle/
├── agents/
│   ├── agent_1_technical.py      # Multi-timeframe analysis
│   ├── agent_2_news.py           # Economic calendar scanner
│   └── agent_3_sentiment.py      # USD strength & risk tone
├── brain/
│   ├── brain.py                  # MiniMax M2.5 integration
│   └── mt5_executor.py           # MT5 trade execution
├── orchestrator_kimi.py          # Main coordinator
├── output/                       # Logs & decision files
├── USAGE.md                      # Detailed documentation
└── README.md                     # This file
```

---

## 📈 Performance Tracking

### Output Files

All decisions and analyses are logged:

- `llm_decision_kimi_*.json` - Each MiniMax decision
- `*_technical.json` - Per-symbol technical analysis
- `learning_log.jsonl` - Training data for future fine-tuning

### Example Output

```bash
$ ls the_oracle/output/

EURUSD_20260305_175610_technical.json
GBPUSD_20260305_175610_technical.json
llm_decision_kimi_20260305_175610.json
```

---

## 🛠️ Development

### Adding New Symbols

Edit `orchestrator_kimi.py`:
```python
symbols=['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'EURJPY']
```

### Adjusting Confidence Threshold

Edit `brain/brain.py`:
```python
if decision['confidence'] < 75:  # Change this
    decision['decision'] = 'NO_TRADE'
```

### Modifying SL/TP

Edit `orchestrator_kimi.py`:
```python
'position': {
    'lot_size': decision['lot_size'],
    'sl_pips': 50,   # Stop loss
    'tp_pips': 100   # Take profit
}
```

---

## ⚠️ Risk Disclaimer

**IMPORTANT:**

1. **AI Decision Authority**: MiniMax makes trading decisions without traditional risk management oversight
2. **Demo Account**: Currently tested only on demo accounts
3. **No Guarantees**: Past performance does not indicate future results
4. **Monitor Closely**: Manual supervision recommended, especially initially
5. **Market Risk**: Forex trading carries significant risk of loss

**Use at your own risk.**

---

## 🔧 Troubleshooting

### "LLM failed" Error
- Check OPENROUTER_API_KEY is set
- Verify internet connection
- MiniMax may be slow - retry

### "Empty content from LLM"
- MiniMax sometimes returns thinking text
- System auto-retries on next cycle

### Trade Execution Fails
- Ensure MT5 is running
- Check account connection
- Verify trading hours for symbol

---

## 🗺️ Roadmap

- [ ] Fine-tune MiniMax with trade outcomes
- [ ] Add auto-breakeven and trailing stops
- [ ] Expand to more symbols (indices, commodities)
- [ ] Add position management (partial closes)
- [ ] Create web dashboard for monitoring
- [ ] Add backtesting capability
- [ ] Multi-account support

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- **MiniMax** for the M2.5 language model
- **OpenRouter** for API access
- **MetaQuotes** for MetaTrader 5
- **Pepperstone** for broker integration

---

**THE ORACLE v3.2**  
*Built with Python, powered by AI, trading the markets.*

Developed: March 2025
