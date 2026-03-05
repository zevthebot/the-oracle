#!/usr/bin/env python3
"""THE ORACLE - AI Brain v4.1 (Simplified)

MiniMax M2.5 powered trading decisions - streamlined prompt.
"""

import json
import os
import re
from typing import Dict, List, Optional
from datetime import datetime
import requests

class OracleBrainLLM:
    """AI Brain - MiniMax M2.5"""
    
    def __init__(self, model: str = "minimax/minimax-m2.5"):
        self.model = model
        self.api_key = self._load_api_key()
        self.base_url = "https://openrouter.ai/api/v1"
    
    def _load_api_key(self) -> str:
        key = os.getenv("OPENROUTER_API_KEY", "")
        if not key:
            try:
                with open(os.path.expanduser("~/.openclaw/openclaw.json")) as f:
                    config = json.load(f)
                    key = config.get("env", {}).get("OPENROUTER_API_KEY", "")
            except:
                pass
        if not key:
            raise ValueError("No OPENROUTER_API_KEY found!")
        return key
    
    def get_open_positions(self) -> str:
        """Get simple list of open trades"""
        try:
            import MetaTrader5 as mt5
            if not mt5.initialize():
                return "None"
            
            positions = mt5.positions_get()
            if not positions:
                mt5.shutdown()
                return "None"
            
            summary = []
            for p in positions:
                summary.append(f"{p.symbol} {p.volume} lots")
            
            mt5.shutdown()
            return ", ".join(summary)
        except:
            return "None"
    
    def build_simple_prompt(self, signals: Dict, balance: float) -> str:
        """Build simplified, focused prompt"""
        
        # Get current signals in simple format
        signal_lines = []
        for symbol, data in signals.get('technical', {}).items():
            dir = data.get('direction', 'NEUTRAL')
            conf = data.get('confidence', 0) * 100
            signal_lines.append(f"{symbol}: {dir} {conf:.0f}%")
        
        signals_str = "\n".join(signal_lines) if signal_lines else "No signals"
        
        # Get open positions
        open_pos = self.get_open_positions()
        
        # Build compact prompt
        prompt = f"""You are THE ORACLE - expert forex trader. Analyze and decide NOW.

ACCOUNT:
- Balance: ${balance:.2f}
- Open: {open_pos}
- Max Daily Loss: 4%
- Goal: 10% profit

MARKET NOW:
{signals_str}

USD: {signals.get('sentiment', {}).get('usd_strength', 50)}/100
Risk: {signals.get('sentiment', {}).get('risk_tone', 'MIXED')}

RULES:
1. TRADE only if setup score >= 75
2. Prefer confidence 80%+ 
3. Lot: 0.1-0.5 based on conviction
4. NO trade if drawdown approaching 4%

DECIDE:
Reply ONLY with valid JSON (no other text):
{{"decision": "TRADE", "symbol": "GBPUSD", "direction": "SELL", "lot_size": 0.3, "confidence": 85, "reasoning": "short reason"}}"""
        
        return prompt
    
    def call_llm(self, prompt: str) -> Optional[Dict]:
        """Call MiniMax via OpenRouter"""
        try:
            print("[Brain] Sending to MiniMax...")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://openclaw.local"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert forex trader. Output ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 400
                },
                timeout=180
            )
            
            print(f"[Brain] Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0].get('message', {})
                
                # MiniMax returns in 'reasoning' field, not 'content'
                content = message.get('content', '') or message.get('reasoning', '')
                content = content.strip() if content else ''
                
                # DEBUG: Log what we received
                print(f"[Brain] Raw response length: {len(content)}")
                print(f"[Brain] First 200 chars: {content[:200]}")
                
                if not content:
                    print("[Brain] Empty response from LLM")
                    return None
                
                # Clean JSON
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                content = content.strip()
                
                # Parse JSON - try multiple methods
                try:
                    # Try direct parse
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Try to find JSON in text
                    json_match = re.search(r'\{[^{}]*"decision"[^{}]*\}', content, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group(0))
                        except:
                            pass
                    
                    # Last resort: extract fields individually
                    decision_match = re.search(r'"decision"\s*:\s*"(\w+)"', content)
                    if decision_match:
                        decision = decision_match.group(1)
                        symbol_match = re.search(r'"symbol"\s*:\s*"([^"]*)"', content)
                        direction_match = re.search(r'"direction"\s*:\s*"(\w+)"', content)
                        lot_match = re.search(r'"lot_size"\s*:\s*([0-9.]+)', content)
                        conf_match = re.search(r'"confidence"\s*:\s*([0-9]+)', content)
                        
                        return {
                            'decision': decision,
                            'symbol': symbol_match.group(1) if symbol_match else None,
                            'direction': direction_match.group(1) if direction_match else None,
                            'lot_size': float(lot_match.group(1)) if lot_match else 0.2,
                            'confidence': int(conf_match.group(1)) if conf_match else 75,
                            'reasoning': 'Extracted from MiniMax response'
                        }
            
            print(f"[Brain] Error or timeout")
            return None
            
        except Exception as e:
            print(f"[Brain] Exception: {e}")
            return None
    
    def make_decision(self, signals: Dict, balance: float) -> Dict:
        """Make trading decision"""
        
        prompt = self.build_simple_prompt(signals, balance)
        llm_response = self.call_llm(prompt)
        
        if not llm_response:
            return {
                "decision": "NO_TRADE",
                "symbol": None,
                "direction": None,
                "lot_size": 0,
                "confidence": 0,
                "reasoning": "LLM timeout/error",
                "timestamp": datetime.now().isoformat(),
                "source": "fallback"
            }
        
        # Parse
        decision = {
            "decision": llm_response.get('decision', 'NO_TRADE'),
            "symbol": llm_response.get('symbol'),
            "direction": llm_response.get('direction'),
            "lot_size": float(llm_response.get('lot_size', 0) or 0),
            "confidence": int(llm_response.get('confidence', 0) or 0),
            "reasoning": llm_response.get('reasoning', 'No reason'),
            "timestamp": datetime.now().isoformat(),
            "source": "minimax_v4"
        }
        
        # Safety
        if decision['lot_size'] > 0.5:
            decision['lot_size'] = 0.5
        if decision['confidence'] < 75:
            decision['decision'] = 'NO_TRADE'
        
        if decision['decision'] == 'TRADE':
            print(f"\n[TRADE] {decision['symbol']} {decision['direction']}")
            print(f"  Lot: {decision['lot_size']}, Conf: {decision['confidence']}%")
        else:
            print(f"[NO TRADE] {decision['reasoning'][:60]}")
        
        return decision


OracleBrain = OracleBrainLLM

if __name__ == "__main__":
    print("THE ORACLE v4.1 - Simplified Mode")
    brain = OracleBrainLLM()
    print(f"Model: {brain.model}")
