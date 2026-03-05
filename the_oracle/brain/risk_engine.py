"""
THE ORACLE - Risk Engine
Manages risk parameters, exposure limits, and trade validation
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime, date
import glob


class RiskEngine:
    """
    Risk management engine for THE ORACLE trading system
    Tracks exposure, validates trades against limits
    """
    
    def __init__(self, account_balance: float = 10000):
        self.account_balance = account_balance
        self.initial_balance = account_balance
        
        # Risk parameters
        self.max_risk_per_trade = 2.0  # % of account
        self.max_daily_loss = 5.0  # % of account
        self.max_total_exposure = 10.0  # % in all trades combined
        
        # State tracking
        self.open_trades = []
        self.closed_trades = []
        self.daily_pnl = 0.0
        
        self.load_state()
    
    def load_state(self):
        """Load previous trades and state"""
        # Look for existing risk state
        state_files = glob.glob("the_oracle/output/risk_state_*.json")
        if state_files:
            latest = max(state_files, key=os.path.getctime)
            try:
                with open(latest, 'r') as f:
                    state = json.load(f)
                    self.daily_pnl = state.get('daily_pnl', 0.0)
                    self.open_trades = state.get('open_trades', [])
                    self.closed_trades = state.get('closed_trades', [])
            except:
                pass
    
    def save_state(self):
        """Save current risk state"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "account_balance": self.account_balance,
            "daily_pnl": self.daily_pnl,
            "open_trades": self.open_trades,
            "closed_trades_count": len(self.closed_trades)
        }
        
        filename = f"the_oracle/output/risk_state_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2)
    
    def can_open_trade(self, symbol: str, lot_size: float, 
                       sl_pips: float) -> Dict:
        """
        Check if a trade can be opened based on risk rules
        """
        # Calculate risk amount
        pip_value = 10.0  # $10/pip for 1.0 lot
        risk_amount = lot_size * sl_pips * pip_value
        risk_percent = (risk_amount / self.account_balance) * 100
        
        checks = {
            "risk_per_trade": risk_percent <= self.max_risk_per_trade,
            "daily_loss_limit": self.daily_pnl > -(self.account_balance * self.max_daily_loss / 100),
            "max_positions": len(self.open_trades) < 5,
            "already_in_symbol": symbol not in [t['symbol'] for t in self.open_trades]
        }
        
        can_trade = all(checks.values())
        failed = [k for k, v in checks.items() if not v]
        
        return {
            "can_trade": can_trade,
            "risk_amount": round(risk_amount, 2),
            "risk_percent": round(risk_percent, 2),
            "checks": {
                "passed": [k for k, v in checks.items() if v],
                "failed": failed
            }
        }
    
    def register_trade(self, trade: Dict):
        """Register a new open trade"""
        trade_record = {
            "symbol": trade['symbol'],
            "direction": trade['direction'],
            "lot_size": trade['lot_size'],
            "entry_price": trade['entry_price'],
            "sl_price": trade['sl_price'],
            "risk_amount": trade['risk_amount'],
            "opened_at": datetime.now().isoformat()
        }
        self.open_trades.append(trade_record)
        self.save_state()
    
    def close_trade(self, symbol: str, exit_price: float, pnl: float):
        """Close a trade and update P&L"""
        for i, trade in enumerate(self.open_trades):
            if trade['symbol'] == symbol:
                trade['exit_price'] = exit_price
                trade['pnl'] = pnl
                trade['closed_at'] = datetime.now().isoformat()
                self.closed_trades.append(trade)
                self.open_trades.pop(i)
                self.daily_pnl += pnl
                break
        
        self.save_state()
    
    def get_daily_summary(self) -> Dict:
        """Get daily risk summary"""
        return {
            "date": date.today().isoformat(),
            "account_balance": self.account_balance,
            "initial_balance": self.initial_balance,
            "daily_pnl": round(self.daily_pnl, 2),
            "daily_pnl_percent": round((self.daily_pnl / self.initial_balance) * 100, 2),
            "daily_loss_limit": self.max_daily_loss,
            "trades_today": len(self.closed_trades),
            "open_positions": len(self.open_trades),
            "available_risk": round(self.max_daily_loss - max(0, -self.daily_pnl), 2)
        }
    
    def update_balance(self, new_balance: float):
        """Update account balance (e.g., from MT5)"""
        self.account_balance = new_balance
