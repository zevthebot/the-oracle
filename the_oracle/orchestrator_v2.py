# ... continuarea ...
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
            output_file = f"the_oracle/output/cycle_{timestamp}.json"
            
            try:
                with open(output_file, 'w') as f:
                    json.dump(results, f, indent=2)
            except Exception as e:
                print(f"[WARNING] Could not save cycle: {e}")
            
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
        print("\n[STOPPED] THE ORACLE v2.0 stopped")
        
        # Save final state
        summary = self.risk.get_daily_summary()
        try:
            with open(f"the_oracle/output/final_summary_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
                json.dump(summary, f, indent=2)
        except:
            pass
        
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
