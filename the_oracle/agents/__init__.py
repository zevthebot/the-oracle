"""
THE ORACLE Trading System - Agents Module

Agent 1: Technical Analysis (agent_1_technical.py)
- Multi-timeframe technical analysis
- Indicator calculations: MA, RSI, MACD, Bollinger, ATR, ADX
- Pattern detection: flags, channels, support/resistance
- Outputs structured JSON for downstream agents
"""

from .agent_1_technical import TechnicalAnalyzer, MultiTimeframeAnalysis, TimeFrameAnalysis

__all__ = [
    'TechnicalAnalyzer',
    'MultiTimeframeAnalysis', 
    'TimeFrameAnalysis',
]
