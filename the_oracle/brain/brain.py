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
        """Build prompt for LLM - FRESH START MODE"""
        
        # FRESH START: Ignore history for win rate, use balance as starting point
        prompt = f"""You are THE ORACLE - expert forex trader. TODAY IS FRESH START.

Starting Balance: ${account_balance:.2f}
Session: NEW (fresh start - ignore previous trades)

## MARKET SIGNALS
"""
        for symbol, data in signals.get('technical', {}).items():
            prompt += f"{symbol}: {data.get('direction')} {data.get('confidence')}%\n"
        
        prompt += f"""
USD: {signals.get('sentiment', {}).get('usd_strength', 50)}/100 | Risk: {signals.get('sentiment', {}).get('risk_tone', 'MIXED')}
News Events: {signals.get('news', {}).get('high_impact_events', 0)}

## DECISION - FRESH START MODE
- Balance ${account_balance:.2f} is your starting capital
- Trade ONLY with confidence > 75%
- Max lot size: 0.5
- NO daily loss limit for this session
- Pick best opportunity from signals

RESPOND WITH JSON ONLY:
{{"decision": "TRADE" or "NO_TRADE", "symbol": "SYMBOL" or null, "direction": "BUY" or "SELL" or null, "lot_size": 0.1-0.5, "confidence": 0-100, "reasoning": "explanation"}}"""
        
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