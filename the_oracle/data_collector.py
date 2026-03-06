#!/usr/bin/env python3
"""THE ORACLE - Data Collector v1.0

Runs every 2 minutes to gather technical data.
Saves to rolling buffer for LLM to read every 15 minutes.
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List

ORACLE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ORACLE_DIR, 'agents'))

from agent_1_technical import TechnicalAnalyzer


class SignalBuffer:
    """Manages rolling buffer of technical signals"""
    
    def __init__(self, buffer_file="output/technical_buffer.jsonl", max_entries=50):
        self.buffer_file = os.path.join(ORACLE_DIR, buffer_file)
        self.max_entries = max_entries  # Keep last 50 readings (~100 min of data)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create buffer file if not exists"""
        os.makedirs(os.path.dirname(self.buffer_file), exist_ok=True)
        if not os.path.exists(self.buffer_file):
            open(self.buffer_file, 'w').close()
    
    def add_reading(self, symbol: str, data: Dict):
        """Add new reading to buffer"""
        reading = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "direction": data.get('direction', 'NEUTRAL'),
            "confidence": data.get('confidence', 0),
            "alignment": data.get('alignment', 0),
            "confluences": data.get('confluences', 0),
            "trend_strength": self._calculate_trend_strength(data)
        }
        
        # Append to file
        with open(self.buffer_file, 'a') as f:
            f.write(json.dumps(reading) + '\n')
        
        # Trim old entries
        self._trim_buffer()
    
    def _calculate_trend_strength(self, data: Dict) -> str:
        """Categorize trend strength"""
        conf = data.get('confidence', 0)
        if conf >= 60:
            return "strong"
        elif conf >= 40:
            return "moderate"
        elif conf >= 25:
            return "weak"
        else:
            return "neutral"
    
    def _trim_buffer(self):
        """Keep only recent entries"""
        try:
            with open(self.buffer_file, 'r') as f:
                lines = f.readlines()
            
            if len(lines) > self.max_entries:
                # Keep last N entries
                lines = lines[-self.max_entries:]
                with open(self.buffer_file, 'w') as f:
                    f.writelines(lines)
        except:
            pass
    
    def get_timeline(self, symbol: str, minutes: int = 30) -> List[Dict]:
        """Get timeline of readings for a symbol"""
        try:
            cutoff_time = datetime.now().timestamp() - (minutes * 60)
            readings = []
            
            with open(self.buffer_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('symbol') == symbol:
                            # Parse timestamp
                            ts = entry.get('timestamp', '')
                            entry_time = datetime.fromisoformat(ts).timestamp()
                            if entry_time >= cutoff_time:
                                readings.append(entry)
                    except:
                        continue
            
            return readings
        except:
            return []
    
    def get_all_current_signals(self) -> Dict[str, List[Dict]]:
        """Get recent signals for all symbols"""
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        return {sym: self.get_timeline(sym, 30) for sym in symbols}


class DataCollector:
    """Continuous data collector - runs every 2 minutes"""
    
    def __init__(self, symbols=None, interval_seconds=120):
        self.symbols = symbols or ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD', 'EURJPY', 'GBPJPY']
        self.interval = interval_seconds
        self.buffer = SignalBuffer()
        self.technical = TechnicalAnalyzer()
        self.running = True
    
    def collect_once(self):
        """Run one collection cycle"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] Collecting data...")
        
        # Connect to MT5
        if not self.technical.connect():
            print("[ERROR] Cannot connect to MT5")
            return
        
        try:
            for symbol in self.symbols:
                try:
                    # Quick technical analysis
                    data = self.technical.analyze_symbol(symbol)
                    if data:
                        # Convert dataclass to dict for buffer
                        data_dict = {
                            'direction': data.recommended_direction,
                            'confidence': round(data.confidence * 100, 1),
                            'alignment': round(data.alignment_score * 100, 1),
                            'confluences': len(data.key_confluences)
                        }
                        self.buffer.add_reading(symbol, data_dict)
                        print(f"  {symbol}: {data_dict['direction']} {data_dict['confidence']}%")
                except Exception as e:
                    print(f"  {symbol}: ERROR - {e}")
        finally:
            # Always disconnect
            self.technical.disconnect()
    
    def run_continuous(self):
        """Run collector in continuous mode"""
        print("=" * 60)
        print("THE ORACLE - Data Collector v1.0")
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Interval: {self.interval} seconds")
        print(f"Buffer: {self.buffer.buffer_file}")
        print("=" * 60)
        
        while self.running:
            try:
                self.collect_once()
                print(f"  → Waiting {self.interval}s until next scan...\n")
                
                # Sleep with interrupt checking
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\nStopping collector...")
                self.running = False
            except Exception as e:
                print(f"Collector error: {e}")
                time.sleep(10)  # Short retry on error
        
        print("Collector stopped.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=120, help='Collection interval in seconds')
    parser.add_argument('--symbols', nargs='+', default=['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'])
    parser.add_argument('--once', action='store_true', help='Run single collection and exit')
    
    args = parser.parse_args()
    
    collector = DataCollector(
        symbols=args.symbols,
        interval_seconds=args.interval
    )
    
    if args.once:
        collector.collect_once()
    else:
        collector.run_continuous()
