#!/usr/bin/env python3
"""
THE ORACLE - Monitor & Auto-Restart System
Checks every hour if THE ORACLE is running, restarts if stopped
"""

import subprocess
import sys
import os
import time
from datetime import datetime
import json

ORACLE_DIR = "C:\\Users\\Claw\\.openclaw\\workspace\\the_oracle"
LOG_FILE = f"{ORACLE_DIR}\\output\\monitor.log"
PID_FILE = f"{ORACLE_DIR}\\oracle.pid"

def log_message(message):
    """Log to file and print"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + "\n")

def is_oracle_running():
    """Check if THE ORACLE orchestrator is running using tasklist"""
    try:
        # Use Windows tasklist to find Python processes
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
            capture_output=True,
            text=True
        )
        
        if 'python.exe' in result.stdout:
            # Check if orchestrator is in command line
            result2 = subprocess.run(
                ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'CommandLine,ProcessId', '/format:csv'],
                capture_output=True,
                text=True
            )
            
            output = result2.stdout
            if 'orchestrator.py' in output and '--continuous' in output:
                # Extract PID
                lines = [l for l in output.strip().split('\n') if l and 'orchestrator' in l.lower()]
                if lines:
                    parts = lines[0].split(',')
                    pid = parts[-1].strip() if len(parts) > 1 else 'unknown'
                    return True, pid
        
        return False, None
        
    except Exception as e:
        log_message(f"[ERROR] Checking process: {e}")
        return False, None

def get_latest_cycle():
    """Check when was the last cycle completed"""
    try:
        output_dir = f"{ORACLE_DIR}\\output"
        files = [f for f in os.listdir(output_dir) if f.startswith('cycle_') and f.endswith('.json')]
        
        if not files:
            return None
        
        # Get most recent file
        files.sort(reverse=True)
        latest = files[0]
        
        # Extract timestamp from filename
        # cycle_YYYYMMDD_HHMMSS.json
        parts = latest.replace('cycle_', '').replace('.json', '').split('_')
        if len(parts) == 2:
            timestamp = f"{parts[0]}_{parts[1]}"
            return timestamp
        
        return latest
    except:
        return None

def restart_oracle():
    """Restart THE ORACLE in continuous mode"""
    try:
        log_message("[RESTART] Initiating THE ORACLE restart...")
        
        # Change to workspace directory
        os.chdir("C:\\Users\\Claw\\.openclaw\\workspace")
        
        # Start orchestrator - detached process
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.Popen(
            [
                sys.executable,
                "the_oracle/orchestrator.py",
                "--continuous",
                "--interval", "15",
                "--symbols", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
                "--balance", "9142"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        # Save PID
        with open(PID_FILE, 'w') as f:
            f.write(str(process.pid))
        
        log_message(f"[RESTART] THE ORACLE restarted with PID: {process.pid}")
        
        # Wait a moment and verify
        time.sleep(3)
        is_running, new_pid = is_oracle_running()
        
        if is_running:
            log_message(f"[SUCCESS] Verified - THE ORACLE running with PID: {new_pid}")
            return True
        else:
            log_message("[WARNING] Process started but verification failed")
            return False
        
    except Exception as e:
        log_message(f"[ERROR] Restart failed: {e}")
        return False

def check_and_maintain():
    """Main monitoring function"""
    log_message("="*60)
    log_message("THE ORACLE - MONITOR CHECK STARTED")
    log_message("="*60)
    
    # Get latest cycle info
    latest_cycle = get_latest_cycle()
    if latest_cycle:
        log_message(f"[INFO] Last cycle: {latest_cycle}")
    
    # Check if running
    is_running, pid = is_oracle_running()
    
    if is_running:
        log_message(f"[OK] THE ORACLE is RUNNING (PID: {pid})")
        log_message("[OK] No action needed")
            
    else:
        log_message("[ALERT] THE ORACLE is NOT RUNNING!")
        log_message("[ACTION] Attempting automatic restart...")
        
        success = restart_oracle()
        if success:
            log_message("[SUCCESS] Restart completed and verified")
        else:
            log_message("[FAILED] Restart attempt failed - will retry next hour")
    
    log_message("="*60)
    log_message("MONITOR CHECK COMPLETED")
    log_message("="*60)
    log_message("")

if __name__ == "__main__":
    check_and_maintain()
