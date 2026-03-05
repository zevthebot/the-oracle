#!/usr/bin/env python3
"""THE ORACLE - Continuous Monitor v2.0 (Dual Process)

Runs two processes in parallel:
1. Data Collector: Every 2 minutes (Python agents)
2. LLM Brain: Every 15 minutes (MiniMax decision)
"""

import subprocess
import time
import sys
import os
from datetime import datetime
import signal
import threading

# Configuration
COLLECTOR_INTERVAL = 120  # 2 minutes
LLM_INTERVAL = 900        # 15 minutes (15 * 60)
BALANCE = 7733
SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']

# Paths
ORACLE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(ORACLE_DIR, "output", "monitor.log")

# Global flags
running = True
collectors_running = False


def log_message(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(log_line + '\n')
    except:
        pass


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global running
    log_message(f"Received signal {signum}, shutting down...")
    running = False


def run_collector_cycle():
    """Run one data collection cycle"""
    try:
        cmd = [
            sys.executable,
            os.path.join(ORACLE_DIR, "data_collector.py"),
            "--once",
            "--symbols"
        ] + SYMBOLS
        
        # Run once (not continuous - we control timing)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Log key outputs
            for line in result.stdout.split('\n'):
                if 'Collecting' in line or ':' in line and any(s in line for s in SYMBOLS):
                    log_message(f"COLLECTOR: {line.strip()}")
            return True
        else:
            log_message(f"Collector error: {result.returncode}")
            return False
            
    except Exception as e:
        log_message(f"Collector exception: {e}")
        return False


def run_llm_cycle():
    """Run one LLM decision cycle"""
    try:
        cmd = [
            sys.executable,
            os.path.join(ORACLE_DIR, "orchestrator_kimi.py"),
            "--balance", str(BALANCE),
            "--symbols"
        ] + SYMBOLS
        
        log_message("=" * 60)
        log_message("Starting LLM Brain cycle...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Log key outputs
        for line in result.stdout.split('\n'):
            if any(k in line for k in ['DECISION', 'TRADE', 'EXECUTED', 'NO_TRADE', 'KIMI']):
                log_message(f"LLM: {line.strip()}")
        
        if result.returncode == 0:
            log_message("LLM cycle completed")
            return True
        else:
            log_message(f"LLM error: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        log_message("LLM cycle timeout")
        return False
    except Exception as e:
        log_message(f"LLM exception: {e}")
        return False


def collector_worker():
    """Worker thread for data collector"""
    global running, collectors_running
    collectors_running = True
    
    log_message("Collector worker started (every 2 min)")
    
    while running:
        try:
            run_collector_cycle()
            
            # Wait 2 minutes
            for _ in range(COLLECTOR_INTERVAL):
                if not running:
                    break
                time.sleep(1)
                
        except Exception as e:
            log_message(f"Collector worker error: {e}")
            time.sleep(30)
    
    collectors_running = False
    log_message("Collector worker stopped")


def main():
    """Main monitor loop"""
    global running
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    log_message("=" * 70)
    log_message("THE ORACLE Monitor v2.0 - Dual Process Mode")
    log_message(f"Data Collection: Every {COLLECTOR_INTERVAL//60} minutes")
    log_message(f"LLM Decisions: Every {LLM_INTERVAL//60} minutes")
    log_message(f"Balance: ${BALANCE}")
    log_message("=" * 70)
    
    # Start collector in separate thread
    collector_thread = threading.Thread(target=collector_worker, daemon=True)
    collector_thread.start()
    
    # Wait for collector to gather some data
    log_message("Waiting for initial data collection...")
    time.sleep(10)  # Give collector time to start
    
    # Main loop for LLM
    next_llm_time = time.time() + LLM_INTERVAL
    
    while running:
        try:
            current_time = time.time()
            
            if current_time >= next_llm_time:
                # Run LLM cycle
                run_llm_cycle()
                next_llm_time = current_time + LLM_INTERVAL
                log_message(f"Next LLM cycle at {datetime.fromtimestamp(next_llm_time).strftime('%H:%M:%S')}")
            
            # Sleep briefly and check again
            time.sleep(5)
            
        except Exception as e:
            log_message(f"Main loop error: {e}")
            time.sleep(10)
    
    log_message("Waiting for collector to stop...")
    time.sleep(2)
    log_message("Monitor stopped")


if __name__ == "__main__":
    main()
