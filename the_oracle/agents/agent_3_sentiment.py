"""
THE ORACLE - Agent 3: Sentiment Analysis Engine
Tracks market sentiment, positioning, and risk flows
"""

import json
import datetime
from typing import Dict, List
import random  # For demo - replace with real data sources in production


class SentimentAnalysisAgent:
    """
    Agent 3: Analyzes market sentiment and risk flows
    Tracks USD strength, risk-on/risk-off, safe haven flows
    """
    
    def __init__(self):
        self.agent_name = "sentiment_analysis"
        self.risk_assets = ['AUD', 'NZD', 'GBP', 'EUR']  # Risk-on currencies
        self.safe_havens = ['JPY', 'CHF', 'USD']  # Risk-off / safe haven
        self.commodity_linked = ['AUD', 'CAD', 'NZD']
        
    def calculate_usd_strength(self) -> Dict:
        """
        Calculate USD strength index (0-100)
        Based on DXY components and major USD pairs
        """
        # In production: fetch real DXY data + USD pairs
        # Simulated calculation for framework
        
        usd_pairs = {
            'EURUSD': 0.30,  # Weight (~inverse)
            'USDJPY': 0.20,
            'GBPUSD': 0.12,
            'USDCAD': 0.09,
            'USDSEK': 0.04,
            'USDCHF': 0.04
        }
        
        # Mock calculations - replace with real MT5 data
        strength = 55 + random.uniform(-10, 10)  # Demo: neutral-bullish USD
        
        return {
            "strength_index": round(strength, 1),
            "trend": "bullish" if strength > 55 else "bearish" if strength < 45 else "neutral",
            "momentum": "increasing" if random.random() > 0.5 else "decreasing",
            "key_drivers": ["Rates differential", "Risk sentiment", "Safe haven flows"]
        }
    
    def detect_risk_tone(self) -> Dict:
        """
        Detect if market is in risk-on or risk-off mode
        """
        # Analyze major pairs behavior
        # Risk-on: AUD, NZD, GBP gain vs USD, JPY, CHF
        # Risk-off: Opposite
        
        tone_score = random.uniform(0, 100)  # Demo
        
        if tone_score > 65:
            tone = "RISK_ON"
            description = "Risk appetite high - favor risk currencies (AUD, NZD, GBP)"
        elif tone_score < 35:
            tone = "RISK_OFF"
            description = "Risk aversion - favor safe havens (JPY, CHF, USD)"
        else:
            tone = "MIXED"
            description = "Mixed sentiment - neutral risk tone"
            
        return {
            "tone": tone,
            "score": round(tone_score, 1),
            "description": description,
            "favored_currencies": self._get_favored_currencies(tone),
            "disfavored_currencies": self._get_disfavored_currencies(tone)
        }
    
    def _get_favored_currencies(self, tone: str) -> List[str]:
        """Get favored currencies based on risk tone"""
        if tone == "RISK_ON":
            return ['AUD', 'NZD', 'GBP']
        elif tone == "RISK_OFF":
            return ['JPY', 'CHF', 'USD']
        return []
    
    def _get_disfavored_currencies(self, tone: str) -> List[str]:
        """Get disfavored currencies based on risk tone"""
        if tone == "RISK_ON":
            return ['JPY', 'CHF']
        elif tone == "RISK_OFF":
            return ['AUD', 'NZD', 'GBP']
        return []
    
    def analyze_pair_sentiment(self, symbol: str) -> Dict:
        """
        Analyze sentiment for specific currency pair
        """
        base = symbol[:3]
        quote = symbol[3:]
        
        usd_data = self.calculate_usd_strength()
        risk_tone = self.detect_risk_tone()
        
        # Calculate pair-specific sentiment
        sentiment_score = 50  # Neutral baseline
        
        # USD pairs
        if quote == 'USD':
            sentiment_score = 100 - usd_data['strength_index']  # Inverse
        elif base == 'USD':
            sentiment_score = usd_data['strength_index']
        else:
            # Cross pair - compare relative strength
            sentiment_score = random.uniform(40, 60)
        
        # Adjust for risk tone
        if base in risk_tone['favored_currencies']:
            sentiment_score += 10
        if quote in risk_tone['favored_currencies']:
            sentiment_score -= 10
        if base in risk_tone['disfavored_currencies']:
            sentiment_score -= 10
        if quote in risk_tone['disfavored_currencies']:
            sentiment_score += 10
            
        # Clamp to 0-100
        sentiment_score = max(0, min(100, sentiment_score))
        
        if sentiment_score > 60:
            bias = "BULLISH"
        elif sentiment_score < 40:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
            
        return {
            "symbol": symbol,
            "sentiment_score": round(sentiment_score, 1),
            "bias": bias,
            "usd_context": usd_data['trend'],
            "risk_tone": risk_tone['tone'],
            "confidence": round(min(abs(sentiment_score - 50) * 2, 100), 1)
        }
    
    def scan_all_sentiment(self, symbols: List[str] = None) -> Dict:
        """
        Main scan function - returns complete sentiment analysis
        """
        if symbols is None:
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
            
        usd_strength = self.calculate_usd_strength()
        risk_tone = self.detect_risk_tone()
        
        pair_analysis = {}
        for symbol in symbols:
            pair_analysis[symbol] = self.analyze_pair_sentiment(symbol)
        
        # Overall market sentiment
        bullish_count = sum(1 for p in pair_analysis.values() if p['bias'] == 'BULLISH')
        bearish_count = sum(1 for p in pair_analysis.values() if p['bias'] == 'BEARISH')
        
        if bullish_count > bearish_count:
            overall = "BULLISH_OVERALL"
        elif bearish_count > bullish_count:
            overall = "BEARISH_OVERALL"
        else:
            overall = "MIXED_OVERALL"
        
        return {
            "agent": self.agent_name,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "usd_strength": usd_strength,
            "risk_tone": risk_tone,
            "pair_analysis": pair_analysis,
            "overall_sentiment": overall,
            "trading_bias": self._generate_trading_bias(risk_tone, usd_strength)
        }
    
    def _generate_trading_bias(self, risk_tone: Dict, usd_strength: Dict) -> str:
        """Generate overall trading bias recommendation"""
        if risk_tone['tone'] == 'RISK_ON' and usd_strength['trend'] == 'bearish':
            return "FAVOR_USD_SELLING_RISK_BUYING"
        elif risk_tone['tone'] == 'RISK_OFF' and usd_strength['trend'] == 'bullish':
            return "FAVOR_USD_BUYING_SAFE_HAVENS"
        else:
            return "NEUTRAL_SELECTIVE_OPPORTUNITIES"
    
    def save_analysis(self, analysis: Dict, symbol: str = None):
        """Save analysis to JSON file"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        symbol_suffix = f"_{symbol}" if symbol else "_all"
        filename = f"the_oracle/output/{symbol_suffix}_{timestamp}_sentiment.json"
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
            
        return filename


if __name__ == "__main__":
    # Test the agent
    agent = SentimentAnalysisAgent()
    
    # Test on all pairs
    result = agent.scan_all_sentiment(['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'])
    filename = agent.save_analysis(result)
    print(f"Sentiment analysis saved: {filename}")
    print(json.dumps(result, indent=2))
