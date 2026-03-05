"""
THE ORACLE - MT5 Executor
Handles MetaTrader 5 trade execution
"""

from typing import Dict, Optional
from datetime import datetime


class MT5Executor:
    """
    MetaTrader 5 trade executor for THE ORACLE
    Handles connections and trade execution
    """
    
    def __init__(self):
        self.connected = False
        self.connection_error = None
        self.last_error = None
    
    def connect(self) -> bool:
        """
        Connect to MT5 terminal
        """
        try:
            import MetaTrader5 as mt5
            
            if not mt5.terminal_info():
                if not mt5.initialize():
                    self.connection_error = f"Failed to initialize MT5: {mt5.last_error()}"
                    return False
            
            self.connected = True
            return True
            
        except ImportError:
            self.connection_error = "MetaTrader5 module not installed"
            # For testing/demo, simulate connection
            self.connected = True
            return True
        except Exception as e:
            self.connection_error = str(e)
            # For testing/demo, simulate connection
            self.connected = True
            return True
    
    def disconnect(self):
        """Disconnect from MT5"""
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
        except:
            pass
        self.connected = False
    
    def execute_trade(self, trade_plan: Dict) -> Dict:
        """
        Execute a trade in MT5
        """
        if not self.connected:
            return {
                "status": "FAILED",
                "reason": "Not connected to MT5"
            }
        
        try:
            import MetaTrader5 as mt5
            
            symbol = trade_plan['symbol']
            direction = trade_plan['direction']
            lot_size = trade_plan['position']['lot_size']
            
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {
                    "status": "FAILED", 
                    "reason": f"Symbol {symbol} not found"
                }
            
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    return {
                        "status": "FAILED",
                        "reason": f"Cannot select symbol {symbol}"
                    }
            
            # Determine order type
            order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
            
            # Get current price
            price = symbol_info.ask if direction == "BUY" else symbol_info.bid
            
            # Calculate SL/TP
            point = symbol_info.point
            sl_pips = trade_plan['position']['sl_pips']
            
            if direction == "BUY":
                sl_price = price - sl_pips * 10 * point
                tp1_price = price + sl_pips * 15 * point  # 1.5 R
            else:
                sl_price = price + sl_pips * 10 * point
                tp1_price = price - sl_pips * 15 * point
            
            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "sl": sl_price,
                "tp": tp1_price,
                "deviation": 20,
                "magic": 123456,
                "comment": "ORACLE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                return {
                    "status": "EXECUTED",
                    "symbol": symbol,
                    "direction": direction,
                    "lot_size": lot_size,
                    "entry_price": price,
                    "sl_price": sl_price,
                    "tp_price": tp1_price,
                    "ticket": result.order,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "FAILED",
                    "reason": f"Order failed: {result.retcode}",
                    "symbol": symbol
                }
                
        except ImportError:
            # Simulation mode for testing
            return self._simulate_execution(trade_plan)
        except Exception as e:
            return {
                "status": "FAILED",
                "reason": str(e),
                "symbol": trade_plan['symbol']
            }
    
    def _simulate_execution(self, trade_plan: Dict) -> Dict:
        """
        Simulate trade execution for testing without MT5
        """
        import random
        
        symbol = trade_plan['symbol']
        direction = trade_plan['direction']
        lot_size = trade_plan['position']['lot_size']
        
        # Simulate entry price
        base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'USDJPY': 150.50,
            'AUDUSD': 0.6550
        }
        
        price = base_prices.get(symbol, 1.0000)
        price += (random.random() - 0.5) * 0.0010  # Small random variation
        
        sl_pips = trade_plan['position']['sl_pips']
        
        # Calculate SL
        if direction == "BUY":
            sl_price = price - sl_pips * 0.0001
        else:
            sl_price = price + sl_pips * 0.0001
        
        return {
            "status": "EXECUTED",
            "symbol": symbol,
            "direction": direction,
            "lot_size": lot_size,
            "entry_price": round(price, 5),
            "sl_price": round(sl_price, 5),
            "tp_price": None,
            "ticket": random.randint(1000000, 9999999),
            "timestamp": datetime.now().isoformat(),
            "simulated": True
        }
    
    def get_account_info(self) -> Optional[Dict]:
        """Get MT5 account information"""
        try:
            import MetaTrader5 as mt5
            
            if not self.connect():
                return None
            
            info = mt5.account_info()
            if info is None:
                return None
            
            return {
                "balance": info.balance,
                "equity": info.equity,
                "margin": info.margin,
                "margin_free": info.margin_free,
                "margin_level": info.margin_level,
                "currency": info.currency
            }
            
        except:
            return None
    
    def get_positions(self) -> List[Dict]:
        """Get open positions"""
        try:
            import MetaTrader5 as mt5
            
            if not self.connect():
                return []
            
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            return [
                {
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "BUY" if pos.type == 0 else "SELL",
                    "volume": pos.volume,
                    "open_price": pos.price_open,
                    "sl": pos.sl,
                    "tp": pos.tp,
                    "pnl": pos.profit
                }
                for pos in positions
            ]
            
        except:
            return []
