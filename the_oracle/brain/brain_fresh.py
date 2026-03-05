#!/usr/bin/env python3
"""THE ORACLE - AI Brain v3.4 (Kimi K2.5 - Parse Text Response)"""

import json
import os
import re
from typing import Dict, Optional
from datetime import datetime
import requests


class OracleBrainLLM:
    """AI Brain - Parse text responses from Kimi K2.5"""
    
    def __init__(self, model: str = "moonshotai/kimi-k2.5"):
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
    
    def build_prompt(self, signals: Dict, balance: float) -> str:
        """Build prompt - ultra simple for Kimi"""
        
        best_signal = None
        best_conf = 0
        for symbol, data in signals.get('technical', {}).items():
            if data.get('confidence', 0) > best_conf:
                best_conf = data.get('confidence', 0)
                best_signal = (symbol, data.get('direction'))
        
        prompt = f"""ACT AS THE ORACLE - Forex Trader. TODAY IS FRESH START.

Balance: ${balance:.2f}
USD: {signals.get('sentiment', {}).get('usd_strength', 50)}/100

BEST SIGNAL: {best_signal[0] if best_signal else 'NONE'} {best_signal[1] if best_signal else ''} ({best_conf}%)

DECISION (reply EXACTLY this format):
ACTION: TRADE or NO_TRADE
SYMBOL: XXXYYY or NONE
DIR: BUY or SELL or NONE
LOT: 0.1-0.5
CONF: 0-100
WHY: brief reason"""
        
        return prompt
    
    def parse_text_response(self, text: str) -> Optional[Dict]:
        """Parse text response from Kimi"""
        try:
            action = re.search(r'ACTION:\s*(\w+)', text, re.IGNORECASE)
            symbol = re.search(r'SYMBOL:\s*(\w+)', text, re.IGNORECASE)
            direction = re.search(r'DIR:\s*(\w+)', text, re.IGNORECASE)
            lot = re.search(r'LOT:\s*([0-9.]+)', text, re.IGNORECASE)
            conf = re.search(r'CONF:\s*([0-9]+)', text, re.IGNORECASE)
            why = re.search(r'WHY:\s*(.+?)(?:\n|$)', text, re.IGNORECASE | re.DOTALL)
            
            return {
                'decision': action.group(1).upper() if action else 'NO_TRADE',
                'symbol': symbol.group(1).upper() if symbol and symbol.group(1).upper() != 'NONE' else None,
                'direction': direction.group(1).upper() if direction and direction.group(1).upper() != 'NONE' else None,
                'lot_size': float(lot.group(1)) if lot else 0.1,
                'confidence': int(conf.group(1)) if conf else 0,
                'reasoning': why.group(1).strip() if why else 'Parsed from text'
            }
        except Exception as e:
            print(f"[Brain] Parse error: {e}")
            return None
    
    def call_llm(self, prompt: str) -> Optional[Dict]:
        """Call Kimi K2.5 via OpenRouter"""
        try:
            print(f"[Brain] Calling Kimi K2.5...")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are THE ORACLE forex trader. Output ONLY valid JSON. No thinking, no explanations, no markdown. Just JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"}
                },
                timeout=90
            )
            
            print(f"[Brain] Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                choices = data.get('choices', [])
                if not choices:
                    return None
                    
                message = choices[0].get('message', {})
                content = message.get('content', '') or message.get('reasoning', '')
                
                # Find the actual decision in the reasoning text
                if 'ACTION:' in content:
                    # Extract from ACTION: onwards
                    content = content[content.find('ACTION:'):]
                    print(f"[Brain] Found decision: {content[:150]}")
                else:
                    print(f"[Brain] No ACTION found in: {content[:200]}")
                    return None
                
                return self.parse_text_response(content)
            else:
                print(f"[Brain] Error: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"[Brain] Exception: {e}")
            return None
    
    def make_decision(self, signals: Dict, balance: float) -> Dict:
        """Make trading decision"""
        
        prompt = self.build_prompt(signals, balance)
        llm_response = self.call_llm(prompt)
        
        if not llm_response:
            return {
                "decision": "NO_TRADE",
                "symbol": None,
                "direction": None,
                "lot_size": 0,
                "confidence": 0,
                "reasoning": "LLM failed",
                "timestamp": datetime.now().isoformat(),
                "source": "fallback"
            }
        
        decision = {
            "decision": llm_response.get('decision', 'NO_TRADE'),
            "symbol": llm_response.get('symbol'),
            "direction": llm_response.get('direction'),
            "lot_size": float(llm_response.get('lot_size', 0)),
            "confidence": int(llm_response.get('confidence', 0)),
            "reasoning": llm_response.get('reasoning', 'No reasoning'),
            "timestamp": datetime.now().isoformat(),
            "source": "llm_kimi_k2.5"
        }
        
        # Safety limits
        if decision['lot_size'] > 0.5:
            decision['lot_size'] = 0.5
        
        if decision['confidence'] < 75:
            decision['decision'] = 'NO_TRADE'
            decision['reasoning'] = f"Low confidence: {decision['confidence']}%"
        
        # Logging
        if decision['decision'] == 'TRADE':
            print(f"\n[TRADE ENTRY]")
            print(f"   {decision['symbol']} {decision['direction']}")
            print(f"   Lot: {decision['lot_size']}, Conf: {decision['confidence']}%")
            print(f"   Why: {decision['reasoning']}")
        else:
            print(f"[NO TRADE]")
        
        return decision


OracleBrain = OracleBrainLLM

if __name__ == "__main__":
    print("AI Brain v3.4 - Kimi K2.5 (Text Parse)")
    brain = OracleBrainLLM()
    print(f"Model: {brain.model}")
