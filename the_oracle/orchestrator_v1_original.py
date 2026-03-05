"""
THE ORACLE - Main Orchestrator
Coordinates all agents, brain, and execution
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Get the directory where this script is located
ORACLE_DIR = os.path.dirname(os.path.abspath(__file__))

# Import all components with absolute paths
sys.path.insert(0, os.path.join(ORACLE_DIR, 'agents'))
sys.path.insert(0, os.path.join(ORACLE_DIR, 'brain'))

from agent_1_technical import TechnicalAnalyzer
from agent_2_news import NewsFundamentalsAgent
from agent_3_sentiment import SentimentAnalysisAgent
from aggregator import SignalAggregator
from brain import OracleBrain
from risk_engine import RiskEngine
from mt5_executor import MT5Executor


class OracleOrchestrator:
    """
    Main orchestrator for THE ORACLE trading system
    Runs the full pipeline: Agents -> Aggregator -> Brain -> Risk -> Execution
    """
    
    def __init__(self, symbols: List[str] = None, account_balance: float = 10000):
        self.symbols = symbols or ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        self.account_balance = account_balance
        
        # Initialize all components
        self.agent_1 = TechnicalAnalyzer()
        self.agent_2 = NewsFundamentalsAgent()
        self.agent_3 = SentimentAnalysisAgent()
        self.aggregator = SignalAggregator()
        self.brain = OracleBrain()
        self.risk = RiskEngine(account_balance=account_balance)
        self.executor = MT5Executor()
        
        self.running = False
        
    def run_scan_cycle(self) -> Dict:
        """
        Run one complete scan cycle
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING",
            "steps": {}
        }
        
        try:
            # Step 1: Run all agents
            print("\n" + "="*60)
            print("THE ORACLE - SCAN CYCLE STARTED")
            print("="*60)
            
            print("\n[1/6] Running Technical Agent...")
            agent_1_results = self.agent_1.scan_and_save_all()
            results['steps']['agent_1'] = f"Processed {len(agent_1_results)} symbols"
            print(f"  [OK] Technical analysis complete")
            
            print("\n[2/6] Running News Agent...")
            agent_2_results = self.agent_2.scan_all_news()
            results['steps']['agent_2'] = f"Found {agent_2_results.get('high_impact_events', 0)} high impact events"
            print(f"  [OK] News analysis complete")
            
            print("\n[3/6] Running Sentiment Agent...")
            agent_3_results = self.agent_3.scan_all_sentiment(self.symbols)
            results['steps']['agent_3'] = f"Risk tone: {agent_3_results['risk_tone']['tone']}"
            print(f"  [OK] Sentiment analysis complete")
            print(f"      USD Strength: {agent_3_results['usd_strength']['strength_index']}")
            print(f"      Risk Tone: {agent_3_results['risk_tone']['tone']}")
            
            # Step 2: Aggregate signals
            print("\n[4/6] Aggregating signals...")
            aggregated = self.aggregator.aggregate_all(self.symbols)
            total_opp = len(aggregated['trade_opportunities'])
            results['steps']['aggregation'] = f"{total_opp} opportunities, {total_opp} selected"
            print(f"  [OK] Aggregation complete")
            print(f"      Total signals: {total_opp}")
            top = aggregated['trade_opportunities'][0] if aggregated['trade_opportunities'] else None
            print(f"      Top opportunity: {top['symbol'] if top else 'NONE'}")
            
            # Step 3: Brain analysis
            print("\n[5/6] Brain analyzing opportunities...")
            brain_decisions = self.brain.scan_all_opportunities(
                self.symbols, 
                self.account_balance
            )
            results['steps']['brain'] = f"{brain_decisions['total_opportunities']} analyzed, {len(brain_decisions['trades'])} approved"
            print(f"  [OK] Brain analysis complete")
            print(f"      Trades approved: {len(brain_decisions['trades'])}")
            
            # Save brain decision
            self.brain.save_decision(brain_decisions)
            
            # Step 4: Check risk and execute
            print("\n[6/6] Risk checks and execution...")
            executed_trades = []
            
            for trade in brain_decisions['trades']:
                symbol = trade['symbol']
                
                # Risk check
                risk_check = self.risk.can_open_trade(
                    symbol, 
                    trade['position']['lot_size'],
                    trade['position']['sl_pips']
                )
                
                if risk_check['can_trade']:
                    # Execute
                    if self.executor.connect():
                        result = self.executor.execute_trade(trade)
                        
                        if result['status'] == 'EXECUTED':
                            # Register with risk engine
                            self.risk.register_trade({
                                'symbol': result['symbol'],
                                'direction': result['direction'],
                                'lot_size': result['lot_size'],
                                'entry_price': result['entry_price'],
                                'sl_price': result['sl_price'],
                                'risk_amount': trade['position']['risk_dollars']
                            })
                            
                            executed_trades.append(result)
                            print(f"  [OK] EXECUTED: {result['symbol']} {result['direction']}")
                        else:
                            print(f"  [FAIL] FAILED: {result['symbol']} - {result.get('reason')}")
                        
                        self.executor.disconnect()
                else:
                    print(f"  [BLOCK] BLOCKED: {symbol} - {risk_check['checks']['failed']}")
            
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
        
        return results
    
    def run_continuous(self, interval_minutes: int = 15):
        """
        Run orchestrator continuously
        """
        self.running = True
        print(f"\n{'='*60}")
        print("THE ORACLE - CONTINUOUS MODE STARTED")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Scan interval: {interval_minutes} minutes")
        print(f"{'='*60}\n")
        
        cycle_count = 0
        
        while self.running:
            cycle_count += 1
            print(f"\n{'='*60}")
            print(f"CYCLE #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            results = self.run_scan_cycle()
            
            # Save cycle results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            with open(f"the_oracle/output/cycle_{timestamp}.json", 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n[WAITING] Next scan in {interval_minutes} minutes...")
            print(f"{'='*60}\n")
            
            # Wait for next cycle
            try:
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                print("\n[STOPPING] Interrupted by user")
                self.stop()
                break
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        print("\n[STOPPED] THE ORACLE orchestrator stopped")
        
        # Save final state
        summary = self.risk.get_daily_summary()
        with open(f"the_oracle/output/final_summary_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Final P&L: ${summary['daily_pnl']:.2f}")
        print(f"Trades today: {summary['trades_today']}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='THE ORACLE Trading System')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=15, help='Scan interval in minutes')
    parser.add_argument('--balance', type=float, default=10000, help='Account balance')
    parser.add_argument('--symbols', nargs='+', default=['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'])
    
    args = parser.parse_args()
    
    orchestrator = OracleOrchestrator(
        symbols=args.symbols,
        account_balance=args.balance
    )
    
    if args.continuous:
        orchestrator.run_continuous(args.interval)
    else:
        # Single scan
        results = orchestrator.run_scan_cycle()
        print(f"\n{'='*60}")
        print("SINGLE SCAN COMPLETE")
        print(f"{'='*60}")
        print(json.dumps(results, indent=2))
