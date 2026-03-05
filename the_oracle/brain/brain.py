#!/usr/bin/env python3
"""THE ORACLE - AI Brain v4.0 (Expert Forex Trader)

MiniMax M2.5 powered trading decisions with senior trader expertise.
Features: Account awareness, risk management, multi-timeframe analysis.
"""

import json
import os
import re
from typing import Dict, List, Optional
from datetime import datetime
import requests

# Try to import MT5 for live account data
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except:
    MT5_AVAILABLE = False


class OracleBrainLLM:
    """AI Brain - Expert Forex Trader powered by MiniMax M2.5"""
    
    def __init__(self, model: str = "minimax/minimax-m2.5"):
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        if not self.api_key:
            try:
                with open(os.path.expanduser("~/.openclaw/openclaw.json")) as f:
                    config = json.load(f)
                    self.api_key = config.get("env", {}).get("OPENROUTER_API_KEY", "")
            except:
                pass
        
        if not self.api_key:
            raise ValueError("No OPENROUTER_API_KEY found!")
        
        self.base_url = "https://openrouter.ai/api/v1"
    
    def get_account_status(self) -> Dict:
        """Get live account status from MT5"""
        try:
            if not MT5_AVAILABLE:
                return {"balance": 0, "equity": 0, "open_trades": [], "daily_dd": 0}
            
            if not mt5.initialize():
                return {"balance": 0, "equity": 0, "open_trades": [], "daily_dd": 0}
            
            account = mt5.account_info()
            positions = mt5.positions_get()
            
            # Calculate daily drawdown
            daily_pnl = sum(p.profit for p in positions) if positions else 0
            daily_dd_pct = (abs(daily_pnl) / account.balance * 100) if account.balance > 0 else 0
            
            result = {
                "balance": account.balance,
                "equity": account.equity,
                "open_pnl": daily_pnl,
                "daily_dd": daily_dd_pct,
                "open_trades": []
            }
            
            if positions:
                for pos in positions:
                    result["open_trades"].append({
                        "ticket": pos.ticket,
                        "symbol": pos.symbol,
                        "type": "BUY" if pos.type == 0 else "SELL",
                        "volume": pos.volume,
                        "open_price": pos.price_open,
                        "current_price": pos.price_current,
                        "profit": pos.profit,
                        "swap": pos.swap
                    })
            
            mt5.shutdown()
            return result
            
        except Exception as e:
            print(f"[Brain] Warning: Could not get account status: {e}")
            return {"balance": 0, "equity": 0, "open_trades": [], "daily_dd": 0}
    
    def read_signal_buffer(self, symbol: str, minutes: int = 30) -> List[Dict]:
        """Read signal timeline from buffer"""
        try:
            buffer_file = "the_oracle/output/technical_buffer.jsonl"
            if not os.path.exists(buffer_file):
                return []
            
            cutoff = datetime.now().timestamp() - (minutes * 60)
            readings = []
            
            with open(buffer_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('symbol') == symbol:
                            ts = datetime.fromisoformat(entry['timestamp']).timestamp()
                            if ts >= cutoff:
                                readings.append(entry)
                    except:
                        continue
            
            return readings
        except:
            return []
    
    def analyze_trend(self, readings: List[Dict]) -> Dict:
        """Analyze trend from buffer readings"""
        if len(readings) < 2:
            return {"direction": "stable", "change": 0, "pattern": "insufficient_data"}
        
        readings_sorted = sorted(readings, key=lambda x: x.get('timestamp', ''))
        first_conf = readings_sorted[0].get('confidence', 0)
        last_conf = readings_sorted[-1].get('confidence', 0)
        change = last_conf - first_conf
        
        if change > 10:
            trend_dir = "accelerating"
        elif change > 5:
            trend_dir = "strengthening"
        elif change < -10:
            trend_dir = "decelerating"
        elif change < -5:
            trend_dir = "weakening"
        else:
            trend_dir = "stable"
        
        confidences = [r.get('confidence', 0) for r in readings_sorted]
        if len(confidences) >= 3:
            if all(confidences[i] <= confidences[i+1] for i in range(len(confidences)-1)):
                pattern = "strong_momentum_building"
            elif all(confidences[i] >= confidences[i+1] for i in range(len(confidences)-1)):
                pattern = "momentum_fading"
            elif confidences[-1] == max(confidences):
                pattern = "at_peak"
            elif confidences[-1] == min(confidences):
                pattern = "at_bottom"
            else:
                pattern = "consolidating"
        else:
            pattern = "building"
        
        return {
            "direction": trend_dir,
            "change": change,
            "pattern": pattern,
            "readings_count": len(readings),
            "current_strength": readings_sorted[-1].get('trend_strength', 'moderate')
        }
    
    def build_timeline_summary(self, symbol: str) -> str:
        """Build timeline summary for a symbol"""
        readings = self.read_signal_buffer(symbol, 30)
        
        if not readings:
            return f"{symbol}: No recent data"
        
        current = readings[-1]
        trend = self.analyze_trend(readings)
        
        if len(readings) >= 2:
            points = []
            for r in readings[-5:]:
                time_str = r['timestamp'][11:16]
                points.append(f"{time_str}:{r['confidence']:.0f}%")
            timeline = " → ".join(points)
            
            summary = f"""{symbol}: {current['direction']} {current['confidence']:.0f}% ({trend['current_strength']})
  Timeline: {timeline}
  Pattern: {trend['pattern'].replace('_', ' ').upper()} | Change: {trend['change']:+.0f}% | Trend: {trend['direction'].upper()}"""
        else:
            summary = f"{symbol}: {current['direction']} {current['confidence']:.0f}% - Building data"
        
        return summary
    
    def calculate_target_metrics(self, balance: float) -> Dict:
        """Calculate target metrics for 10% profit goal"""
        target_profit = balance * 0.10
        daily_target = target_profit / 14  # 2 weeks aggressive target
        
        return {
            "target_profit_10pct": target_profit,
            "target_profit_formatted": f"${target_profit:.2f}",
            "estimated_timeframe": "2-4 weeks (aggressive but controlled)",
            "daily_profit_target": daily_target,
            "risk_per_trade_pct": 0.5  # 0.5% per trade
        }
    
    def build_enriched_prompt(self, signals: Dict, account_balance: float) -> str:
        """Build expert-level prompt with full context"""
        
        # Get live account data
        account = self.get_account_status()
        balance = account.get('balance', account_balance) or account_balance
        equity = account.get('equity', balance)
        open_pnl = account.get('open_pnl', 0)
        daily_dd = account.get('daily_dd', 0)
        open_trades = account.get('open_trades', [])
        
        # Calculate targets
        metrics = self.calculate_target_metrics(balance)
        
        # Build open positions section
        positions_section = ""
        if open_trades:
            positions_section = "\n[OPEN POSITIONS]\n"
            total_volume = 0
            for trade in open_trades:
                positions_section += f"  - {trade['symbol']} {trade['type']} {trade['volume']} lots @ {trade['open_price']:.5f}\n"
                positions_section += f"    Current: {trade['current_price']:.5f} | P&L: ${trade['profit']:.2f}\n"
                total_volume += trade['volume']
            positions_section += f"  Total Volume: {total_volume:.2f} lots | Unrealized P&L: ${open_pnl:.2f}\n"
            
            # Check correlations
            symbols_open = [t['symbol'] for t in open_trades]
            if len(set(symbols_open)) == 1:
                positions_section += f"  [WARNING] CONCENTRATION RISK: All trades on {symbols_open[0]}\n"
        else:
            positions_section = "\n[OPEN POSITIONS] None (fresh start)\n"
        
        # Build market analysis section
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        market_sections = []
        
        for symbol in symbols:
            market_sections.append(self.build_timeline_summary(symbol))
        
        market_analysis = "\n\n".join(market_sections)
        
        # Find best momentum opportunity
        best_setup = None
        best_score = 0
        for symbol in symbols:
            readings = self.read_signal_buffer(symbol, 30)
            if readings:
                trend = self.analyze_trend(readings)
                current_conf = readings[-1].get('confidence', 0)
                # Score = confidence + momentum bonus
                score = current_conf + (trend['change'] if trend['change'] > 0 else 0)
                if score > best_score:
                    best_score = score
                    best_setup = {
                        'symbol': symbol,
                        'confidence': current_conf,
                        'trend': trend
                    }
        
        hot_opportunity = ""
        if best_setup and best_setup['trend']['change'] > 10:
            hot_opportunity = f"""
[HOT OPPORTUNITY]
{best_setup['symbol']} showing STRONG MOMENTUM (+{best_setup['trend']['change']:.0f}% confidence gain)
Pattern: {best_setup['trend']['pattern'].replace('_', ' ').upper()}
"""
        
        # Build final prompt
        prompt = f"""You are THE ORACLE - A SENIOR FOREX TRADER with 15+ years experience.
You have managed $100M+ portfolios with consistent profitability.
You combine technical mastery with market intuition and iron discipline.

================================================================
ACCOUNT STATUS
================================================================
Balance: ${balance:.2f}
Equity: ${equity:.2f}
Daily Drawdown: {daily_dd:.2f}% (MAX ALLOWED: 4.0%)
{positions_section}

================================================================
STRATEGIC OBJECTIVES
================================================================
PRIMARY GOAL: Achieve 10% profit = ${metrics['target_profit_formatted']}
Target Timeline: 2-4 weeks (aggressive but controlled)
Daily Profit Target: ${metrics['daily_profit_target']:.2f}
Risk Per Trade: {metrics['risk_per_trade_pct']:.1f}%

================================================================
MARKET INTELLIGENCE (Multi-Timeframe Analysis)
================================================================
{market_analysis}

{hot_opportunity}

================================================================
MACRO CONTEXT
================================================================
USD Strength: {signals.get('sentiment', {}).get('usd_strength', 50)}/100
Risk Tone: {signals.get('sentiment', {}).get('risk_tone', 'MIXED')}
High Impact Events: {signals.get('news', {}).get('high_impact_events', 0)}

================================================================
TRADING PRINCIPLES (NEVER VIOLATE)
================================================================
1. CAPITAL PROTECTION > Profit (Max 4% daily drawdown hard limit)
2. QUALITY > Quantity (Only A+ setups, 75+ score minimum)
3. MOMENTUM > Prediction (Follow the trend, don't fight it)
4. CORRELATION AWARENESS (Don't stack same-direction trades)
5. DISCIPLINE > Emotion (Stick to rules, exit when wrong)

SETUP SCORING:
- Multi-timeframe confluence: +30 points
- Accelerating momentum: +25 points
- USD/Risk alignment: +20 points
- No opposing positions: +15 points
- Good timing (avoid news/weekend): +10 points

================================================================
DECISION FRAMEWORK
================================================================
IF Trade Score >= 75:
  - direction: "BUY" or "SELL"
  - lot_size: 0.1-0.5 (based on conviction: 75-85=0.2, 85-95=0.3, 95+=0.5)
  - confidence: score (75-100)
  - reasoning: Explain the setup, momentum, and risk management

IF Trade Score < 75 OR Daily DD >= 4%:
  - decision: "NO_TRADE"
  - reasoning: Explain what you're waiting for

IF Positions Already Open:
  - Evaluate if adding improves or hurts portfolio
  - Consider taking profits on existing before opening new

================================================================
OUTPUT FORMAT (JSON ONLY)
================================================================
{{"decision": "TRADE" or "NO_TRADE", "symbol": "XXXYYY" or null, "direction": "BUY" or "SELL" or null, "lot_size": 0.1-0.5, "confidence": 75-100, "reasoning": "Detailed explanation with technical justification"}}"""
        
        return prompt
    
    def call_llm(self, prompt: str) -> Optional[Dict]:
        """Call MiniMax M2.5 via OpenRouter"""
        try:
            print("[Brain] Consulting MiniMax Expert Trader...")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://openclaw.local",
                    "X-Title": "THE ORACLE Trading"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert forex trading AI. Output valid JSON only. Be decisive and professional."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 800
                },
                timeout=180
            )
            
            print(f"[Brain] Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                choices = result.get('choices', [])
                if not choices:
                    return None
                
                message = choices[0].get('message', {})
                content = message.get('content') or message.get('reasoning', '')
                
                if not content:
                    print("[Brain] Empty response")
                    return None
                
                # Parse JSON with fallback
                content = content.strip()
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                # Handle incomplete JSON
                if not content.endswith('}'):
                    # Try regex extraction for key fields
                    decision_match = re.search(r'"decision"\s*:\s*"(\w+)"', content)
                    if decision_match:
                        return {
                            'decision': decision_match.group(1),
                            'symbol': None,
                            'direction': None,
                            'lot_size': 0,
                            'confidence': 0,
                            'reasoning': 'Partial JSON - using safe defaults'
                        }
                    content = content.rstrip() + ', "reasoning": "completed"}'
                
                try:
                    decision = json.loads(content)
                    print(f"[Brain] Decision: {decision.get('decision')}")
                    return decision
                except:
                    # Last resort extraction
                    if '"decision": "TRADE"' in content:
                        return {'decision': 'TRADE', 'symbol': None, 'direction': None, 'lot_size': 0.3, 'confidence': 80, 'reasoning': 'Emergency parse'}
                    return {'decision': 'NO_TRADE', 'symbol': None, 'direction': None, 'lot_size': 0, 'confidence': 0, 'reasoning': 'Parse error'}
            else:
                print(f"[Brain] API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[Brain] Exception: {e}")
            return None
    
    def make_decision(self, signals: Dict, account_balance: float) -> Dict:
        """Make trading decision with full context"""
        
        # Build enriched prompt
        prompt = self.build_enriched_prompt(signals, account_balance)
        
        # Call LLM
        llm_response = self.call_llm(prompt)
        
        if not llm_response:
            return {
                "decision": "NO_TRADE",
                "symbol": None,
                "direction": None,
                "lot_size": 0,
                "confidence": 0,
                "reasoning": "LLM communication failed",
                "timestamp": datetime.now().isoformat(),
                "source": "fallback"
            }
        
        # Parse and validate
        lot_size = float(llm_response.get('lot_size', 0) or 0)
        confidence = int(llm_response.get('confidence', 0) or 0)
        
        # Default lot if missing
        if lot_size == 0 and llm_response.get('decision') == 'TRADE':
            lot_size = 0.3
        
        decision = {
            "decision": llm_response.get('decision', 'NO_TRADE'),
            "symbol": llm_response.get('symbol'),
            "direction": llm_response.get('direction'),
            "lot_size": lot_size,
            "confidence": confidence,
            "reasoning": llm_response.get('reasoning', 'No reasoning provided'),
            "timestamp": datetime.now().isoformat(),
            "source": "minimax_expert_v4"
        }
        
        # Hard safety limits
        if decision['lot_size'] > 0.5:
            decision['lot_size'] = 0.5
            decision['reasoning'] += " [LOT SIZE CAPPED TO 0.5]"
        
        # Enforce minimum confidence
        if decision['confidence'] < 75:
            decision['decision'] = 'NO_TRADE'
            decision['reasoning'] = f"Blocked: confidence {decision['confidence']}% below 75% threshold"
        
        # Check daily drawdown limit (4%)
        account = self.get_account_status()
        if account.get('daily_dd', 0) >= 4.0:
            decision['decision'] = 'NO_TRADE'
            decision['reasoning'] = f"STOPPED: Daily drawdown {account['daily_dd']:.2f}% reached 4% limit"
        
        # Log decision
        if decision['decision'] == 'TRADE':
            print(f"\n[TRADE SIGNAL]")
            print(f"   {decision['symbol']} {decision['direction']}")
            print(f"   Lot: {decision['lot_size']}, Confidence: {decision['confidence']}%")
            print(f"   Reason: {decision['reasoning'][:100]}...")
        else:
            print(f"[NO TRADE] {decision['reasoning'][:80]}...")
        
        return decision


OracleBrain = OracleBrainLLM

if __name__ == "__main__":
    print("THE ORACLE v4.0 - Expert Forex Trader AI")
    brain = OracleBrainLLM()
    print(f"Model: {brain.model}")
    print("Ready for trading decisions with full market context.")
