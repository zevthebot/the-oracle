"""
THE ORACLE - Aggregator v1
Combines signals from all agents into unified trading decisions
"""

import json
import datetime
from typing import Dict, List, Tuple, Optional
import os
import glob


class SignalAggregator:
    """
    Aggregates output from Agent 1 (Technical), Agent 2 (News), Agent 3 (Sentiment)
    Creates unified signal with confidence score and trade recommendation
    """
    
    def __init__(self, output_dir: str = "the_oracle/output"):
        self.output_dir = output_dir
        self.weights = {
            "technical": 0.40,  # Agent 1
            "news": 0.35,       # Agent 2
            "sentiment": 0.25   # Agent 3
        }
    
    def _find_latest_analysis(self, symbol: str, agent_type: str) -> Optional[Dict]:
        """Find latest analysis file for symbol and agent type"""
        pattern = f"{self.output_dir}/{symbol}_*_{agent_type}.json"
        files = glob.glob(pattern)
        
        if not files:
            return None
            
        # Get most recent file
        latest = max(files, key=os.path.getctime)
        
        with open(latest, 'r') as f:
            return json.load(f)
    
    def _calculate_technical_score(self, tech_data: Dict) -> Tuple[float, str]:
        """Calculate normalized technical score (0-100)"""
        if not tech_data or 'bias' not in tech_data:
            return 50, "NEUTRAL"
            
        bias = tech_data.get('bias', 'NEUTRAL')
        confidence = tech_data.get('confidence', 50)
        
        if bias == "BULLISH":
            score = 50 + (confidence / 2)  # 50-100
        elif bias == "BEARISH":
            score = 50 - (confidence / 2)  # 0-50
        else:
            score = 50
            
        return score, bias
    
    def _calculate_news_score(self, news_data: Dict) -> Tuple[float, str]:
        """Calculate news impact score"""
        if not news_data:
            return 50, "NEUTRAL"
            
        events = news_data.get('events', [])
        recommendation = news_data.get('trading_recommendation', 'NO_MAJOR_EVENTS')
        
        if recommendation == "AVOID_TRADING_HIGH_IMPACT_COLLISION":
            return 50, "NEUTRAL"  # Neutral = avoid
        elif recommendation == "WAIT_FOR_EVENT_RELEASE":
            return 50, "NEUTRAL"
        
        # Calculate based on high impact events
        high_impact_count = news_data.get('high_impact_events', 0)
        
        if high_impact_count > 0:
            # Check if any bullish/bearish bias in events
            return 50, "NEUTRAL"  # Uncertain
        
        return 50, "NEUTRAL"
    
    def _calculate_sentiment_score(self, sent_data: Dict) -> Tuple[float, str]:
        """Calculate sentiment score"""
        if not sent_data:
            return 50, "NEUTRAL"
            
        bias = sent_data.get('bias', 'NEUTRAL')
        score = sent_data.get('sentiment_score', 50)
        
        return score, bias
    
    def aggregate_symbol(self, symbol: str) -> Dict:
        """
        Aggregate all agent outputs for a specific symbol
        """
        # Load agent outputs
        tech_data = self._find_latest_analysis(symbol, 'technical')
        news_data = self._find_latest_analysis(symbol, 'news')
        sent_data = self._find_latest_analysis(symbol, 'sentiment')
        
        # If no data found, try symbol-specific from sentiment
        if not sent_data:
            # Try finding in multi-symbol sentiment file
            all_sent = self._find_latest_analysis(None, 'sentiment')
            if all_sent and 'pair_analysis' in all_sent:
                sent_data = all_sent['pair_analysis'].get(symbol, {})
        
        # Calculate individual scores
        tech_score, tech_bias = self._calculate_technical_score(tech_data)
        news_score, news_bias = self._calculate_news_score(news_data)
        sent_score, sent_bias = self._calculate_sentiment_score(sent_data)
        
        # Weighted aggregate score
        # Score: 0-100 (0=strong sell, 50=neutral, 100=strong buy)
        weighted_score = (
            tech_score * self.weights['technical'] +
            news_score * self.weights['news'] +
            sent_score * self.weights['sentiment']
        )
        
        # Determine final bias
        if weighted_score > 60:
            final_bias = "BUY"
            strength = (weighted_score - 60) / 40  # 0-1
        elif weighted_score < 40:
            final_bias = "SELL"
            strength = (40 - weighted_score) / 40  # 0-1
        else:
            final_bias = "NEUTRAL"
            strength = 0
        
        # Calculate overall confidence
        confidences = []
        if tech_data and 'confidence' in tech_data:
            confidences.append(tech_data['confidence'])
        if sent_data and 'confidence' in sent_data:
            confidences.append(sent_data['confidence'])
        if news_data and 'high_impact_events' in news_data:
            # Lower confidence if high impact events pending
            if news_data['high_impact_events'] == 0:
                confidences.append(70)
            else:
                confidences.append(40)
        
        overall_confidence = sum(confidences) / len(confidences) if confidences else 50
        
        # Risk assessment
        risk_factors = []
        if news_data and news_data.get('high_impact_events', 0) > 0:
            risk_factors.append("HIGH_IMPACT_NEWS_PENDING")
        if tech_data and tech_data.get('vol', 0) > 50:  # High volatility
            risk_factors.append("HIGH_VOLATILITY")
        if abs(weighted_score - 50) < 10:  # Close to neutral
            risk_factors.append("LOW_CONVICTION")
        
        return {
            "symbol": symbol,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "aggregate_score": round(weighted_score, 1),
            "bias": final_bias,
            "strength": round(strength, 2),
            "confidence": round(overall_confidence, 1),
            "recommendation": self._generate_recommendation(final_bias, strength, overall_confidence, risk_factors),
            "component_scores": {
                "technical": {
                    "score": round(tech_score, 1),
                    "bias": tech_bias,
                    "weight": self.weights['technical']
                },
                "news": {
                    "score": round(news_score, 1),
                    "bias": news_bias,
                    "weight": self.weights['news']
                },
                "sentiment": {
                    "score": round(sent_score, 1),
                    "bias": sent_bias,
                    "weight": self.weights['sentiment']
                }
            },
            "risk_factors": risk_factors,
            "trade_parameters": self._generate_trade_params(final_bias, tech_data, overall_confidence)
        }
    
    def _generate_recommendation(self, bias: str, strength: float, confidence: float, risks: List) -> str:
        """Generate final trade recommendation"""
        if confidence < 50:
            return "SKIP_LOW_CONFIDENCE"
        
        if risks and "HIGH_IMPACT_NEWS_PENDING" in risks:
            return "WAIT_FOR_NEWS_CLEARANCE"
        
        if bias == "NEUTRAL":
            return "NO_TRADE_NEUTRAL"
        
        if strength > 0.7 and confidence > 65:
            return f"EXECUTE_{bias}_STRONG"
        elif strength > 0.4 and confidence > 55:
            return f"EXECUTE_{bias}_MODERATE"
        else:
            return f"REDUCE_SIZE_{bias}_WEAK"
    
    def _generate_trade_params(self, bias: str, tech_data: Dict, confidence: float) -> Dict:
        """Generate suggested entry/SL/TP levels"""
        if bias == "NEUTRAL":
            return {}
        
        params = {
            "risk_percent": round(min(confidence / 10, 2.0), 1),  # Max 2% risk
        }
        
        # Get levels from technical if available
        if tech_data:
            if bias == "BUY" and 'tp_levels' in tech_data:
                params['tp1'] = tech_data['tp_levels'][0] if tech_data['tp_levels'] else None
                params['tp2'] = tech_data['tp_levels'][1] if len(tech_data['tp_levels']) > 1 else None
            elif bias == "SELL" and 'tp_levels' in tech_data:
                params['tp1'] = tech_data['tp_levels'][0] if tech_data['tp_levels'] else None
                params['tp2'] = tech_data['tp_levels'][1] if len(tech_data['tp_levels']) > 1 else None
            
            if 'sl_suggestion' in tech_data:
                params['sl'] = tech_data['sl_suggestion']
        
        return params
    
    def aggregate_all(self, symbols: List[str] = None) -> Dict:
        """
        Aggregate signals for all symbols
        """
        if symbols is None:
            symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        
        aggregated_signals = {}
        trade_opportunities = []
        
        for symbol in symbols:
            signal = self.aggregate_symbol(symbol)
            aggregated_signals[symbol] = signal
            
            # Check if it's a trade opportunity
            if 'EXECUTE' in signal['recommendation']:
                trade_opportunities.append({
                    "symbol": symbol,
                    "direction": signal['bias'],
                    "confidence": signal['confidence'],
                    "risk": signal['risk_factors']
                })
        
        # Sort by confidence
        trade_opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "symbols": symbols,
            "signals": aggregated_signals,
            "trade_opportunities": trade_opportunities[:3],  # Top 3
            "market_bias": self._determine_market_bias(aggregated_signals)
        }
    
    def _determine_market_bias(self, signals: Dict) -> str:
        """Determine overall market bias"""
        buy_count = sum(1 for s in signals.values() if s['bias'] == 'BUY')
        sell_count = sum(1 for s in signals.values() if s['bias'] == 'SELL')
        
        if buy_count > sell_count:
            return f"BULLISH_DOMINANT_{buy_count}vs{sell_count}"
        elif sell_count > buy_count:
            return f"BEARISH_DOMINANT_{sell_count}vs{buy_count}"
        else:
            return "BALANCED_MARKET"
    
    def save_aggregate(self, data: Dict, filename: str = None):
        """Save aggregated signals to file"""
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.output_dir}/signals_aggregated_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename


if __name__ == "__main__":
    # Run aggregator
    agg = SignalAggregator()
    
    result = agg.aggregate_all(['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'])
    
    filename = agg.save_aggregate(result)
    print(f"Aggregated signals saved: {filename}")
    print("\n=== TOP TRADE OPPORTUNITIES ===")
    for opp in result['trade_opportunities']:
        print(f"{opp['symbol']}: {opp['direction']} (confidence: {opp['confidence']}%)")
    
    print(f"\nMarket Bias: {result['market_bias']}")
