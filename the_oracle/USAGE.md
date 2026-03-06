# THE ORACLE - Usage Documentation
## Multi-Agent AI Trading System with LLM Brain

**Version:** 3.2 - MiniMax M2.5 LLM Mode  
**Active Period:** March 2026  
**Account:** Pepperstone Demo 62108425  
**Mode:** Fresh Start (LLM Authority)  
**Symbols:** 8 pairs (EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, NZDUSD, EURJPY, GBPJPY)  
**Confidence Threshold:** 65%  
**LLM Timeout:** 300 seconds (5 minutes)

---

## 🎯 System Overview

THE ORACLE is an AI-powered trading system where **MiniMax M2.5** has final decision authority:

- **3 Data Agents:** Gather market intelligence
  - Technical Analysis (multi-timeframe)
  - News & Fundamentals  
  - Market Sentiment
- **LLM Brain:** MiniMax M2.5 analyzes signals and decides
- **Direct Execution:** No risk engine override - LLM has full control
- **MT5 Integration:** Live execution on Pepperstone

---

## 🏗️ Architecture

```
the_oracle/
├── agents/
│   ├── agent_1_technical.py    # Multi-timeframe analysis (D1/H4/H1/M15)
│   ├── agent_2_news.py         # Economic calendar & events
│   └── agent_3_sentiment.py    # USD strength & risk tone
├── brain/
│   ├── brain.py                # MiniMax M2.5 LLM decision engine
│   └── mt5_executor.py         # MT5 trade execution
├── orchestrator_kimi.py        # Main coordinator
└── output/                     # Signal & decision logs
```

---

## 🚀 Running THE ORACLE

### Quick Start
```bash
cd the_oracle
python orchestrator_kimi.py --balance 7733
```

### With Custom Parameters
```bash
python orchestrator_kimi.py \
  --balance 7733 \
  --symbols EURUSD GBPUSD USDJPY AUDUSD
```

### Full Options
```bash
python orchestrator_kimi.py \
  --balance 7733 \
  --symbols EURUSD GBPUSD USDJPY AUDUSD
```

**Parameters:**
- `--balance`: Current account balance (required)
- `--symbols`: Trading pairs to analyze (default: 4 majors)

---

## 🧠 How It Works

### Step 1: Data Collection (Agents)
**Agent 1 - Technical:**
- Analyzes D1, H4, H1, M15 timeframes
- Trend detection with confidence scoring
- Outputs: Direction (BUY/SELL/SIDEWAYS), Confidence %, Confluences

**Agent 2 - News:**
- Scans economic calendar
- High impact events detection
- Outputs: Event count, volatility bias

**Agent 3 - Sentiment:**
- USD strength index (0-100)
- Risk tone (RISK_ON/RISK_OFF/MIXED)
- Outputs: USD reading, market sentiment

### Step 2: LLM Analysis (MiniMax M2.5)
All signals sent to MiniMax M2.5 via OpenRouter:
```
Starting Balance: $XXXX
Session: NEW (fresh start)

GBPUSD: SELL 58.5%
EURUSD: SELL 37.5%
USDJPY: BUY 40.5%
AUDUSD: SELL 37.5%

USD: 50.2/100 | Risk: RISK_OFF
News: 1 events
```

**MiniMax decides:**
- `decision`: TRADE or NO_TRADE
- `symbol`: Which pair
- `direction`: BUY or SELL
- `lot_size`: 0.1 - 0.5
- `confidence`: 0-100
- `reasoning`: Why

### Step 3: Direct Execution
- If MiniMax says TRADE → Execute immediately
- No risk engine override
- SL: 50 pips (fixed for now)
- TP: 1.5x SL (75 pips)

---

## ⚙️ Configuration

### Current Settings (March 2026)
```json
{
  "account": 62108425,
  "server": "PepperstoneUK-Demo",
  "llm_model": "minimax/minimax-m2.5",
  "llm_provider": "OpenRouter",
  "symbols": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "EURJPY", "GBPJPY"],
  "mode": "fresh_start",
  "daily_loss_limit": "DISABLED",
  "risk_engine_override": "DISABLED",
  "max_lot": 0.5,
  "min_confidence": 65,
  "llm_timeout_seconds": 300
}
```

### Fresh Start Mode
- ❌ No daily loss tracking from previous sessions
- ❌ No win/loss history affects decisions
- ✅ Balance provided = Starting capital for this session
- ✅ MiniMax evaluates each opportunity fresh

### LLM Authority Mode
- ❌ Risk engine cannot block trades
- ❌ No max risk per trade limits
- ❌ No correlation checks
- ✅ MiniMax decides lot size (0.1-0.5)
- ✅ MiniMax decides if trade is worth taking

---

## 📊 Trade Management

### Entry Logic (MiniMax decides)
- Minimum confidence: 75% (enforced)
- Direction: BUY or SELL
- Lot size: 0.1 - 0.5 (MiniMax chooses)

### Stop Loss & Take Profit (System sets)
- **SL:** 50 pips (fixed)
- **TP:** 75 pips (1.5x SL)

### Position Management
- Manual monitoring recommended
- No auto breakeven (yet)
- No trailing stop (yet)

---

## 📋 Output & Logs

### Decision Logs
Located in `the_oracle/output/`:
- `llm_decision_kimi_YYYYMMDD_HHMMSS.json` - Each MiniMax decision
- `EURUSD_YYYYMMDD_HHMMSS_technical.json` - Technical analysis per symbol
- `learning_log.jsonl` - Decisions for future training

### Example Decision Output
```json
{
  "timestamp": "2026-03-05T17:56:16",
  "decision": "TRADE",
  "symbol": "GBPUSD",
  "direction": "SELL",
  "lot_size": 0.3,
  "confidence": 78,
  "reasoning": "GBPUSD shows strongest SELL signal at 0.585%...",
  "source": "llm_minimax_m2.5"
}
```

---

## ⚠️ Important Notes

### LLM Limitations
- MiniMax sometimes returns truncated JSON (handled by parser)
- Response time: 30-90 seconds
- Occasional "thinking" text instead of pure JSON (filtered)

### Risk Disclaimer
- **LLM makes final decisions** - not traditional risk management
- Demo account only during testing
- Monitor trades manually
- MiniMax can theoretically suggest any lot 0.1-0.5

### Fresh Start Implications
- Previous losses don't stop trading
- No "daily loss limit" protection
- Each run is independent

---

## 🔧 Troubleshooting

### "LLM failed" Error
- Check OpenRouter API key
- Check internet connection
- Retry - MiniMax can be slow

### "Empty content from LLM"
- MiniMax returned thinking text instead of JSON
- System will retry on next cycle

### Trade Not Executed
- Check MT5 is running
- Check account connection
- Verify symbol is available

---

## 📈 Future Improvements

- [ ] Add auto-breakeven after +X pips
- [ ] Add trailing stop option
- [ ] Fine-tune MiniMax with trade outcomes
- [ ] Add more symbols (EURJPY, GBPJPY, etc.)
- [ ] Create feedback loop for LLM learning

---

**THE ORACLE v3.2 - MiniMax M2.5 Mode**  
*Fresh Start | LLM Authority | Direct Execution*

Last Updated: March 5, 2026
