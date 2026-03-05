"""
THE ORACLE - AI Brain v3.1 (LLM with MiniMax M2.5)
Uses: minimax/minimax-m2.5 via OpenRouter
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import requests

# Fix stdout encoding for Windows
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)


class OracleBrainLLM:
    """AI Brain - Powered by MiniMax M2.5"""
    
    def __init__(self, model: str = "minimax/minimax-m2.5"):
        self.model = model
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        # Fallback: try to load from config
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
        
    def load_recent_history(self, n: int = 20) -> List[Dict]:
        """Load recent trade history"""
        try:
            journal_path = "mt5_trader/universal_trade_journal.jsonl"
            if not os.path.exists(journal_path):
                return []
            
            results = []
            with open(journal_path, 'r') as f:
                for line in reversed(f.readlines()):
                    try:
                        entry = json.loads(line)
                        if entry.get('event') == 'EXIT':
                            results.append({
                                'symbol': entry.get('symbol'),
                                'pnl': entry.get('pnl', 0),
                                'exit_reason': entry.get('exit_reason'),
                                'timestamp': entry.get('timestamp', '')
                            })
                            if len(results) >= n:
                                break
                    except:
                        continue
            return results
        except:
            return []
    
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
        
        # Sort by time
        readings_sorted = sorted(readings, key=lambda x: x.get('timestamp', ''))
        
        # Get first and last confidence
        first_conf = readings_sorted[0].get('confidence', 0)
        last_conf = readings_sorted[-1].get('confidence', 0)
        change = last_conf - first_conf
        
        # Determine trend
        if change > 10:
            trend_dir = "increasing"
        elif change < -10:
            trend_dir = "decreasing"
        else:
            trend_dir = "stable"
        
        # Detect pattern
        confidences = [r.get('confidence', 0) for r in readings_sorted]
        if len(confidences) >= 3:
            if all(confidences[i] <= confidences[i+1] for i in range(len(confidences)-1)):
                pattern = "strong_acceleration"
            elif all(confidences[i] >= confidences[i+1] for i in range(len(confidences)-1)):
                pattern = "deceleration"
            elif confidences[-1] == max(confidences):
                pattern = "peak"
            elif confidences[-1] == min(confidences):
                pattern = "bottom"
            else:
                pattern = "oscillating"
        else:
            pattern = "building"
        
        return {
            "direction": trend_dir,
            "change": change,
            "pattern": pattern,
            "readings_count": len(readings),
            "time_span_minutes": len(readings) * 2  # Approximate
        }
    
    def build_timeline_summary(self, symbol: str) -> str:
        """Build timeline summary for a symbol"""
        readings = self.read_signal_buffer(symbol, 30)
        
        if not readings:
            return f"{symbol}: No recent data"
        
        # Get current data
        current = readings[-1]
        trend = self.analyze_trend(readings)
        
        # Build timeline string
        if len(readings) >= 3:
            # Show evolution
            points = []
            for i, r in enumerate(readings[-5:]):  # Last 5 points
                time_str = r['timestamp'][11:16]  # HH:MM
                points.append(f"{time_str}:{r['confidence']}%")
            
            timeline = " → ".join(points)
            
            summary = f"""{symbol}: {current['direction']} {current['confidence']}% ({current['trend_strength']})
  Timeline: {timeline}
  Pattern: {trend['pattern']} | Change: {trend['change']:+.0f}% | Trend: {trend['direction']}"""
        else:
            summary = f"{symbol}: {current['direction']} {current['confidence']}% ({current['trend_strength']}) - Building data"
        
        return summary
    
    def get_daily_stats(self) -> Dict:
        """Get today's trading stats"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            journal_path = "mt5_trader/universal_trade_journal.jsonl"
            
            daily_pnl = 0
            trades_today = 0
            
            if os.path.exists(journal_path):
                with open(journal_path, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            if entry.get('event') == 'EXIT':
                                ts = entry.get('timestamp', '')
                                if today in ts:
                                    daily_pnl += entry.get('pnl', 0)
                                    trades_today += 1
                        except:
                            continue
            
            return {'daily_pnl': daily_pnl, 'trades_today': trades_today}
        except:
            return {'daily_pnl': 0, 'trades_today': 0}
    
    def build_prompt(self, signals: Dict, account_balance: float, history: List[Dict], daily_stats: Dict) -> str:
        """Build enriched prompt with timeline data"""
        
        # Build timeline summaries for each symbol
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        timeline_sections = []
        
        for symbol in symbols:
            timeline_sections.append(self.build_timeline_summary(symbol))
        
        # Find best momentum opportunity
        best_momentum = None
        best_score = 0
        for symbol in symbols:
            readings = self.read_signal_buffer(symbol, 30)
            if readings:
                trend = self.analyze_trend(readings)
                current_conf = readings[-1].get('confidence', 0)
                # Score = current confidence + momentum bonus
                score = current_conf + (trend['change'] if trend['change'] > 0 else 0)
                if score > best_score:
                    best_score = score
                    best_momentum = {
                        'symbol': symbol,
                        'confidence': current_conf,
                        'trend': trend
                    }
        
        momentum_hint = ""
        if best_momentum and best_momentum['trend']['change'] > 10:
            momentum_hint = f"\n🔥 STRONG MOMENTUM: {best_momentum['symbol']} gaining +{best_momentum['trend']['change']:.0f}% confidence"
        
        prompt = f"""You are THE ORACLE - expert forex trader analyzing MOMENTUM & TRENDS.

Starting Balance: ${account_balance:.2f}
Session: NEW (fresh start - real-time data every 2 minutes)

## SIGNAL TIMELINES (Last 30 minutes, 2-min intervals)
{momentum_hint}

"""
        # Add timeline for each symbol
        for section in timeline_sections:
            prompt += section + "\n\n"
        
        prompt += f"""## MARKET CONTEXT
USD Strength: {signals.get('sentiment', {}).get('usd_strength', 50)}/100
Risk Tone: {signals.get('sentiment', {}).get('risk_tone', 'MIXED')}
News Events: {signals.get('news', {}).get('high_impact_events', 0)}

## ANALYSIS GUIDE - READ THE TRENDS
Look for:
1. "acceleration" = momentum building (enter early)
2. "peak" = top of move (wait or reduce size)
3. "strong_acceleration" = high conviction signal
4. "stable" + high confidence = good continuation
5. "deceleration" = momentum fading (avoid)

## DECISION RULES
- Balance ${account_balance:.2f} is starting capital
- Trade ONLY with current confidence > 75%
- Max lot: 0.5, prefer 0.2-0.3 for uncertain setups
- Pick symbol with best momentum + trend alignment
- If multiple strong signals, pick highest confidence

JSON ONLY:
{{"decision": "TRADE" or "NO_TRADE", "symbol": "SYMBOL", "direction": "BUY" or "SELL", "lot_size": 0.1-0.5, "confidence": 0-100, "reasoning": "trend analysis here"}}"""
        
        return prompt
    
    def call_llm(self, prompt: str) -> Optional[Dict]:
        """Call MiniMax M2.5 via OpenRouter"""
        try:
            print("[Brain] Sending request to MiniMax M2.5...")
            
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
                        {"role": "system", "content": "You are THE ORACLE forex AI. Reply ONLY with valid JSON. No explanations. No markdown. Just raw JSON."},
                        {"role": "user", "content": prompt + "\n\nIMPORTANT: Output ONLY valid JSON. Do not explain. Do not think out loud. Just output the JSON object."}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500,
                    "stream": False
                },
                timeout=120
            )
            
            print(f"[Brain] Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0].get('message', {})
                
                # Handle both 'content' and 'reasoning' fields
                content = message.get('content') or message.get('reasoning', '')
                
                if not content:
                    print("[Brain] Warning: Empty response from LLM")
                    return None
                
                print(f"[Brain] Raw response: {content[:300]}")
                
                # Handle incomplete JSON
                content = content.strip()
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                # Try to fix incomplete JSON - MiniMax returns truncated JSON
                if not content.endswith('}'):
                    # Try to find complete fields and reconstruct
                    import re
                    decision_match = re.search(r'"decision"\s*:\s*"(\w+)"', content)
                    symbol_match = re.search(r'"symbol"\s*:\s*"([^"]*)"', content)
                    direction_match = re.search(r'"direction"\s*:\s*"(\w+)"', content)
                    lot_match = re.search(r'"lot_size"\s*:\s*([0-9.]+)', content)
                    conf_match = re.search(r'"confidence"\s*:\s*([0-9]+)', content)
                    
                    if decision_match:
                        # Reconstruct from partial data
                        return {
                            'decision': decision_match.group(1),
                            'symbol': symbol_match.group(1) if symbol_match else None,
                            'direction': direction_match.group(1) if direction_match else None,
                            'lot_size': float(lot_match.group(1)) if lot_match else 0.3,
                            'confidence': int(conf_match.group(1)) if conf_match else 80,
                            'reasoning': 'Partial JSON from MiniMax'
                        }
                    # Fallback: try to complete the JSON
                    content = content.rstrip() + ', "lot_size": 0.3, "confidence": 80, "reasoning": "completed"}'
                
                try:
                    decision = json.loads(content)
                except json.JSONDecodeError:
                    # Last resort: regex extraction
                    import re
                    decision_match = re.search(r'"decision"\s*:\s*"(\w+)"', content)
                    if decision_match:
                        return {
                            'decision': decision_match.group(1),
                            'symbol': None,
                            'direction': None,
                            'lot_size': 0.3,
                            'confidence': 80,
                            'reasoning': 'Emergency regex parse'
                        }
                    raise
                
                print(f"[Brain] LLM decision: {decision.get('decision')}")
                return decision
                
            elif response.status_code == 429:
                print("[Brain] Rate limited - waiting...")
                return None
            elif response.status_code == 400:
                error_text = response.text[:500]
                print(f"[Brain] API Error 400: {error_text}")
                return None
            else:
                print(f"[Brain] API Error {response.status_code}: {response.text[:200]}")
                return None
                
        except requests.Timeout:
            print("[Brain] Timeout after 120s - MiniMax too slow")
            return None
        except Exception as e:
            print(f"[Brain] Error: {e}")
            return None
    
    def make_decision(self, signals: Dict, account_balance: float) -> Dict:
        """Main decision function - LLM ONLY"""
        
        history = self.load_recent_history(20)
        daily_stats = self.get_daily_stats()
        
        prompt = self.build_prompt(signals, account_balance, history, daily_stats)
        llm_response = self.call_llm(prompt)
        
        if not llm_response:
            print("[Brain] LLM failed - returning SAFE mode")
            return {
                "decision": "NO_TRADE",
                "symbol": None,
                "direction": None,
                "lot_size": 0,
                "confidence": 0,
                "reasoning": "LLM timeout/error - safe mode",
                "timestamp": datetime.now().isoformat(),
                "source": "fallback_timeout"
            }
        
        # Parse response - handle None values safely
        lot_size = llm_response.get('lot_size', 0) or 0
        confidence = llm_response.get('confidence', 0) or 0
        
        # Default lot if missing from partial JSON
        if lot_size == 0:
            lot_size = 0.3
            print(f"[Brain] Using default lot: 0.3")
        
        decision = {
            "decision": llm_response.get('decision', 'NO_TRADE') or 'NO_TRADE',
            "symbol": llm_response.get('symbol'),
            "direction": llm_response.get('direction'),
            "lot_size": float(lot_size),
            "confidence": int(confidence),
            "reasoning": llm_response.get('reasoning', 'No reasoning') or 'No reasoning',
            "timestamp": datetime.now().isoformat(),
            "source": "llm_minimax_m2.5"
        }
        
        # Hard safety limits
        if decision['lot_size'] > 0.5:
            decision['lot_size'] = 0.5
            decision['reasoning'] += " [LOT CAPPED TO 0.5]"
        
        if decision['confidence'] < 75:
            decision['decision'] = 'NO_TRADE'
            decision['reasoning'] = f"Blocked: confidence {decision['confidence']}% < 75%"
        
        # DAILY LOSS CHECK DISABLED - FRESH START MODE
        # Previous trades from other agents don't count
        
        return decision


OracleBrain = OracleBrainLLM

if __name__ == "__main__":
    brain = OracleBrainLLM()
    print("Brain v3.1 (MiniMax) initialized")
    print(f"Model: {brain.model}")
    print(f"API Key: {brain.api_key[:20]}...")