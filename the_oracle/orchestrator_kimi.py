#!/usr/bin/env python3
"""THE ORACLE v3.2 - Orchestrator with Kimi K2.5"""

import sys
import os
import json
from datetime import datetime
from typing import Dict

ORACLE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ORACLE_DIR, 'agents'))
sys.path.insert(0, os.path.join(ORACLE_DIR, 'brain'))

from agent_1_technical import TechnicalAnalyzer
from agent_2_news import NewsFundamentalsAgent
from agent_3_sentiment import SentimentAnalysisAgent
from brain import OracleBrainLLM
from risk_engine import RiskEngine
from mt5_executor import MT5Executor


class OracleOrchestratorKimi:
    """THE ORACLE with Kimi K2.5 LLM"""
    
    def __init__(self, symbols=None, account_balance=10000):
        self.symbols = symbols or ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        self.account_balance = account_balance
        
        self.agent_1 = TechnicalAnalyzer()
        self.agent_2 = NewsFundamentalsAgent()
        self.agent_3 = SentimentAnalysisAgent()
        self.brain = OracleBrainLLM()
        self.risk = RiskEngine(account_balance=account_balance)
        self.executor = MT5Executor()
        
    def run_scan_cycle(self) -> Dict:
        results = {
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING", 
            "llm_mode": "KIMI_K2.5",
            "steps": {}
        }
        
        try:
            print("\n" + "="*70)
            print("THE ORACLE v3.2 - KIMI K2.5 LLM MODE")
            print("="*70)
            
            # Step 1: Technical Analysis
            print("\n[1/5] Technical Agent analyzing...")
            tech_results = self.agent_1.scan_and_save_all()
            technical_data = {d['symbol']: d for d in tech_results if 'symbol' in d}
            results['steps']['technical'] = f"{len(technical_data)} symbols"
            print(f"  [OK] {len(technical_data)} technical analyses complete")
            
            for symbol, data in technical_data.items():
                print(f"    {symbol}: {data.get('direction')} {data.get('confidence')}%")
            
            # Step 2: News
            print("\n[2/5] News Agent scanning...")
            news = self.agent_2.scan_all_news()
            news_data = {
                'events': news.get('high_impact_events', 0),
                'bias': news.get('news_bias', 'neutral'),
                'recommendation': news.get('trading_recommendation', 'NO_EVENTS')
            }
            results['steps']['news'] = f"{news_data['events']} events"
            print(f"  [OK] News: {news_data['events']} events, bias: {news_data['bias']}")
            
            # Step 3: Sentiment
            print("\n[3/5] Sentiment Agent checking...")
            sentiment = self.agent_3.scan_all_sentiment(self.symbols)
            sentiment_data = {
                'usd_strength': sentiment.get('usd_strength', {}).get('strength_index', 50),
                'risk_tone': sentiment.get('risk_tone', {}).get('tone', 'MIXED')
            }
            results['steps']['sentiment'] = f"USD: {sentiment_data['usd_strength']}, Risk: {sentiment_data['risk_tone']}"
            print(f"  [OK] USD: {sentiment_data['usd_strength']}, Risk: {sentiment_data['risk_tone']}")
            
            # Step 4: LLM Brain (Kimi K2.5)
            print("\n[4/5] [BRAIN] KIMI K2.5 analyzing signals...")
            llm_signals = {
                'technical': technical_data,
                'sentiment': sentiment_data,
                'news': news_data
            }
            
            decision = self.brain.make_decision(llm_signals, self.account_balance)
            
            results['llm_decision'] = decision.get('decision')
            results['llm_reasoning'] = decision.get('reasoning')
            results['llm_confidence'] = decision.get('confidence')
            
            print(f"\n  [OK] KIMI DECISION: {decision['decision']}")
            print(f"  Reasoning: {decision['reasoning']}")
            
            if decision['decision'] == 'TRADE':
                print(f"  [TRADE] {decision['symbol']} {decision['direction']}")
                print(f"  [INFO] Lot: {decision['lot_size']}, Confidence: {decision['confidence']}%")
                print(f"  [NOTE] LLM has final authority - executing without risk engine override")
                
                # Execute directly - MiniMax has full control
                if self.executor.connect():
                    trade_plan = {
                        'symbol': decision['symbol'],
                        'direction': decision['direction'],
                        'position': {
                            'lot_size': decision['lot_size'],
                            'sl_pips': 50
                        },
                        'quality_analysis': {
                            'quality_score': decision['confidence']
                        }
                    }
                    
                    result = self.executor.execute_trade(trade_plan)
                    
                    if result['status'] == 'EXECUTED':
                        results['trade_executed'] = True
                        results['trade_details'] = result
                        print(f"  [OK] EXECUTED: Ticket {result.get('ticket')}")
                    else:
                        results['trade_executed'] = False
                        results['trade_error'] = result.get('reason')
                        print(f"  [FAIL] {result.get('reason')}")
                    
                    self.executor.disconnect()
            else:
                print(f"  [WAIT] NO TRADE - Kimi decided to wait")
            
            results['status'] = "COMPLETE"
            
            # Save decision
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            with open(f"the_oracle/output/llm_decision_kimi_{timestamp}.json", 'w') as f:
                json.dump(decision, f, indent=2)
            
            print("\n" + "="*70)
            print(f"CYCLE COMPLETE - {datetime.now().strftime('%H:%M:%S')}")
            print("="*70)
            
        except Exception as e:
            results['status'] = "ERROR"
            results['error'] = str(e)
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='THE ORACLE v3.2 - Kimi K2.5')
    parser.add_argument('--balance', type=float, default=10000, help='Account balance')
    parser.add_argument('--symbols', nargs='+', default=['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'])
    
    args = parser.parse_args()
    
    orchestrator = OracleOrchestratorKimi(
        symbols=args.symbols,
        account_balance=args.balance
    )
    
    results = orchestrator.run_scan_cycle()
    print("\n" + "="*70)
    print("SCAN COMPLETE")
    print("="*70)
    print(json.dumps(results, indent=2))
