"""
THE ORACLE - Main Orchestrator v2.0 (LLM-Enhanced)
Coordinates all agents, brain (LLM-powered), and execution
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

ORACLE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ORACLE_DIR, 'agents'))
sys.path.insert(0, os.path.join(ORACLE_DIR, 'brain'))

from agent_1_technical import TechnicalAnalyzer
from agent_2_news import NewsFundamentalsAgent
from agent_3_sentiment import SentimentAnalysisAgent
from aggregator import SignalAggregator
from brain_v3 import OracleBrainLLM
from risk_engine import RiskEngine
from mt5_executor import MT5Executor


class OracleOrchestrator:
    def __init__(self, symbols: List[str] = None, account_balance: float = 10000):
        self.symbols = symbols or ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        self.account_balance = account_balance
        self.agent_1 = TechnicalAnalyzer()
        self.agent_2 = NewsFundamentalsAgent()
        self.agent_3 = SentimentAnalysisAgent()
        self.aggregator = SignalAggregator()
        self.brain = OracleBrainLLM()
        self.risk = RiskEngine(account_balance=account_balance)
        self.executor = MT5Executor()
        self.running = False
        
    def run_scan_cycle(self) -> Dict:
        results = {"timestamp": datetime.now().isoformat(), "status": "RUNNING", "steps": {}}
        
        try:
            print("\n" + "="*60)
            print("THE ORACLE v2.0 (LLM) - SCAN CYCLE STARTED")
            print("="*60)
            
            # Step 1: Technical Agent
            print("\n[1/5] Running Technical Agent...")
            agent_1_results = self.agent_1.scan_and_save_all()
            technical_data = {}
            for symbol_data in agent_1_results:
                if 'symbol' in symbol_data:
                    technical_data[symbol_data['symbol']] = symbol_data
            results['steps']['agent_1'] = f"Processed {len(agent_1_results)} symbols"
            print(f"  [OK] Technical analysis complete")
            
            # Step 2: News Agent
            print("\n[2/5] Running News Agent...")
            agent_2_results = self.agent_2.scan_all_news()
            news_data = {
                'news_bias': agent_2_results.get('news_bias', 'neutral'),
                'high_impact_events': agent_2_results.get('high_impact_events', 0),
                'trading_recommendation': agent_2_results.get('trading_recommendation', 'NO_MAJOR_EVENTS')
            }
            results['steps']['agent_2'] = f"Found {news_data['high_impact_events']} high impact events"
            print(f"  [OK] News analysis complete")
            
            # Step 3: Sentiment Agent
            print("\n[3/5] Running Sentiment Agent...")
            agent_3_results = self.agent_3.scan_all_sentiment(self.symbols)
            sentiment_data = {
                'usd_strength': agent_3_results.get('usd_strength', {}).get('strength_index', 50),
                'risk_tone': agent_3_results.get('risk_tone', {}).get('tone', 'MIXED')
            }
            results['steps']['agent_3'] = f"Risk tone: {sentiment_data['risk_tone']}"
            print(f"  [OK] Sentiment analysis complete")
            print(f"      USD Strength: {sentiment_data['usd_strength']}")
            print(f"      Risk Tone: {sentiment_data['risk_tone']}")
            
            # Step 4: LLM Brain
            print("\n[4/5] LLM Brain analyzing signals...")
            llm_signals = {'technical': technical_data, 'sentiment': sentiment_data, 'news': news_data}
            brain_decision = self.brain.make_decision(llm_signals, self.account_balance)
            
            results['steps']['brain'] = f"LLM Decision: {brain_decision.get('decision', 'ERROR')}"
            results['llm_reasoning'] = brain_decision.get('reasoning', 'N/A')
            
            # Save LLM decision separately for audit
            try:
                with open(f"the_oracle/output/llm_decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                    json.dump(brain_decision, f, indent=2)
            except:
                pass
            
            print(f"  [OK] LLM Brain analysis complete")
            print(f"      Decision: {brain_decision.get('decision', 'NO_TRADE')}")
            print(f"      Reasoning: {brain_decision.get('reasoning', 'N/A')[:150]}...")
            if brain_decision.get('decision') == 'TRADE':
                print(f"      Symbol: {brain_decision.get('symbol')}")
                print(f"      Direction: {brain_decision.get('direction')}")
                print(f"      Lot Size: {brain_decision.get('lot_size')}")
                print(f"      Confidence: {brain_decision.get('confidence')}%")
                print(f"      Full Reasoning: {brain_decision.get('reasoning', 'N/A')}")
            
            # Step 5: Risk & Execution
            print("\n[5/5] Risk checks and execution...")
            executed_trades = []
            
            if brain_decision.get('decision') == 'TRADE':
                symbol = brain_decision['symbol']
                risk_check = self.risk.can_open_trade(symbol, brain_decision['lot_size'], 50)
                
                if risk_check['can_trade']:
                    if self.executor.connect():
                        trade_plan = {
                            'symbol': symbol,
                            'direction': brain_decision['direction'],
                            'position': {'lot_size': brain_decision['lot_size'], 'sl_pips': 50},
                            'quality_analysis': {'quality_score': brain_decision.get('confidence', 50)}
                        }
                        result = self.executor.execute_trade(trade_plan)
                        if result['status'] == 'EXECUTED':
                            executed_trades.append(result)
                            print(f"  [OK] EXECUTED: {result['symbol']} {result['direction']}")
                        else:
                            print(f"  [FAIL] {result.get('reason', 'Unknown')}")
                        self.executor.disconnect()
                else:
                    print(f"  [BLOCKED] {symbol}")
            
            results['steps']['execution'] = f"{len(executed_trades)} trades executed"
            results['executed_trades'] = executed_trades
            results['status'] = "COMPLETE"
            
            print("\n" + "="*60)
            print(f"CYCLE COMPLETE - {len(executed_trades)} trades executed")
            print("="*60)
            
        except Exception as e:
            results['status'] = "ERROR"
            results['error'] = str(e)
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def run_continuous(self, interval_minutes: int = 15):
        self.running = True
        print(f"\n{'='*60}")
        print("THE ORACLE v2.0 (LLM-Powered) - CONTINUOUS MODE")
        print(f"{'='*60}\n")
        
        cycle_count = 0
        while self.running:
            cycle_count += 1
            print(f"\n{'='*60}")
            print(f"CYCLE #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            results = self.run_scan_cycle()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"the_oracle/output/cycle_{timestamp}.json"
            try:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)
            except Exception as e:
                print(f"[WARNING] Could not save cycle: {e}")
            
            print(f"\n[WAITING] Next scan in {interval_minutes} minutes...")
            print(f"{'='*60}\n")
            
            try:
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                print("\n[STOPPING] Interrupted by user")
                self.stop()
                break
    
    def stop(self):
        self.running = False
        print("\n[STOPPED] THE ORACLE v2.0 stopped")
        summary = self.risk.get_daily_summary()
        print(f"Final P&L: ${summary['daily_pnl']:.2f}")
        print(f"Trades today: {summary['trades_today']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='THE ORACLE v2.0 - LLM Trading System')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=15, help='Scan interval in minutes')
    parser.add_argument('--balance', type=float, default=10000, help='Account balance')
    parser.add_argument('--symbols', nargs='+', default=['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'])
    args = parser.parse_args()
    
    orchestrator = OracleOrchestrator(symbols=args.symbols, account_balance=args.balance)
    
    if args.continuous:
        orchestrator.run_continuous(args.interval)
    else:
        results = orchestrator.run_scan_cycle()
        print(f"\n{'='*60}")
        print("SINGLE SCAN COMPLETE")
        print(f"{'='*60}")
        print(json.dumps(results, indent=2))
