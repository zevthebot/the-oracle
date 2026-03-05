#!/usr/bin/env python3
"""
THE ORACLE - Agent 1: Technical Analysis
MT5 Technical Analysis Agent for multi-timeframe market analysis

Analyzes: D1, H4, H1, M15 timeframes
Calculates: MA, RSI, MACD, Bollinger Bands, ATR, ADX
Detects: Flags, Channels, Support/Resistance levels
Output: Structured JSON for downstream agents
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import sys
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum

# Add mt5_trader to path for shared utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "mt5_trader"))


class TimeFrame(Enum):
    """MT5 timeframe mappings"""
    D1 = mt5.TIMEFRAME_D1
    H4 = mt5.TIMEFRAME_H4
    H1 = mt5.TIMEFRAME_H1
    M15 = mt5.TIMEFRAME_M15
    M5 = mt5.TIMEFRAME_M5


@dataclass
class IndicatorValues:
    """Container for technical indicator values"""
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    ma_200: Optional[float] = None
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None
    bb_position: Optional[float] = None  # % position within bands
    atr_14: Optional[float] = None
    adx_14: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None


@dataclass
class CandlePattern:
    """Detected candlestick pattern"""
    name: str
    direction: str  # bullish/bearish/neutral
    strength: float  # 0-1
    description: str


@dataclass
class ChartPattern:
    """Detected chart pattern"""
    name: str
    direction: str
    strength: float
    key_levels: List[float]
    description: str


@dataclass
class SupportResistance:
    """Support and Resistance levels"""
    level: float
    type: str  # support/resistance
    strength: float  # based on touches
    touches: int
    timeframe: str


@dataclass
class TimeFrameAnalysis:
    """Complete analysis for a single timeframe"""
    symbol: str
    timeframe: str
    timestamp: str
    current_price: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    indicators: IndicatorValues
    trend: str  # bullish/bearish/sideways
    trend_strength: float
    candle_patterns: List[CandlePattern]
    chart_patterns: List[ChartPattern]
    support_resistance: List[SupportResistance]
    key_levels: Dict[str, float]
    volatility: float
    analysis_summary: str


@dataclass
class MultiTimeframeAnalysis:
    """Aggregated analysis across all timeframes"""
    symbol: str
    timestamp: str
    timeframes: Dict[str, TimeFrameAnalysis]
    overall_bias: str
    confidence: float
    alignment_score: float  # how well timeframes align
    key_confluences: List[str]
    recommended_direction: str
    invalidation_level: float


class TechnicalAnalyzer:
    """Core technical analysis engine"""
    
    def __init__(self, symbols=None):
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
        self.connected = False
        self.results = []
        
    def connect(self) -> bool:
        """Initialize MT5 connection"""
        if not mt5.initialize():
            print(f"[ERROR] MT5 initialization failed: {mt5.last_error()}")
            return False
        
        account_info = mt5.account_info()
        if account_info is None:
            print("[ERROR] MT5 not logged in")
            return False
            
        self.connected = True
        print(f"[OK] MT5 Connected | Account: {account_info.login}")
        return True
    
    def disconnect(self):
        """Shutdown MT5 connection"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("[OK] MT5 Disconnected")
    
    def fetch_data(self, symbol: str, timeframe: int, bars: int = 500) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from MT5"""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) == 0:
            print(f"[WARN] No data for {symbol} on timeframe {timeframe}")
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def calculate_ma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return df['close'].rolling(window=period).mean()
    
    def calculate_ema(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD components"""
        ema_fast = self.calculate_ema(df, fast)
        ema_slow = self.calculate_ema(df, slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def calculate_bollinger(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate ADX, +DI, -DI"""
        # True Range
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Directional Movement
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        plus_dm[plus_dm <= minus_dm] = 0
        minus_dm[minus_dm <= plus_dm] = 0
        
        # Smoothed values
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # ADX
        dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    def detect_candle_patterns(self, df: pd.DataFrame) -> List[CandlePattern]:
        """Detect candlestick patterns"""
        patterns = []
        if len(df) < 3:
            return patterns
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3] if len(df) >= 3 else prev
        
        # Body and shadow calculations
        curr_body = abs(curr['close'] - curr['open'])
        curr_range = curr['high'] - curr['low']
        prev_body = abs(prev['close'] - prev['open'])
        
        upper_shadow = curr['high'] - max(curr['close'], curr['open'])
        lower_shadow = min(curr['close'], curr['open']) - curr['low']
        
        # Doji
        if curr_body <= curr_range * 0.1:
            patterns.append(CandlePattern(
                name="Doji",
                direction="neutral",
                strength=0.6,
                description="Indecision in the market"
            ))
        
        # Hammer / Hanging Man
        if lower_shadow > curr_body * 2 and upper_shadow < curr_body * 0.5:
            if curr['close'] > curr['open']:
                patterns.append(CandlePattern(
                    name="Hammer",
                    direction="bullish",
                    strength=0.7,
                    description="Potential bullish reversal at support"
                ))
            else:
                patterns.append(CandlePattern(
                    name="Hanging Man",
                    direction="bearish",
                    strength=0.6,
                    description="Potential bearish reversal at resistance"
                ))
        
        # Shooting Star / Inverted Hammer
        if upper_shadow > curr_body * 2 and lower_shadow < curr_body * 0.5:
            if curr['close'] < curr['open']:
                patterns.append(CandlePattern(
                    name="Shooting Star",
                    direction="bearish",
                    strength=0.7,
                    description="Potential bearish reversal at resistance"
                ))
            else:
                patterns.append(CandlePattern(
                    name="Inverted Hammer",
                    direction="bullish",
                    strength=0.6,
                    description="Potential bullish reversal"
                ))
        
        # Engulfing
        if curr['close'] > curr['open'] and prev['close'] < prev['open']:
            if curr['open'] < prev['close'] and curr['close'] > prev['open']:
                patterns.append(CandlePattern(
                    name="Bullish Engulfing",
                    direction="bullish",
                    strength=0.8,
                    description="Strong bullish reversal signal"
                ))
        elif curr['close'] < curr['open'] and prev['close'] > prev['open']:
            if curr['open'] > prev['close'] and curr['close'] < prev['open']:
                patterns.append(CandlePattern(
                    name="Bearish Engulfing",
                    direction="bearish",
                    strength=0.8,
                    description="Strong bearish reversal signal"
                ))
        
        # Morning/Evening Star
        if len(df) >= 3:
            small_body = abs(prev['close'] - prev['open']) < prev_body * 0.3 if prev_body > 0 else True
            if small_body:
                if (prev2['close'] < prev2['open'] and 
                    curr['close'] > curr['open'] and 
                    curr['close'] > (prev2['open'] + prev2['close']) / 2):
                    patterns.append(CandlePattern(
                        name="Morning Star",
                        direction="bullish",
                        strength=0.85,
                        description="Strong bullish reversal pattern"
                    ))
                elif (prev2['close'] > prev2['open'] and 
                      curr['close'] < curr['open'] and 
                      curr['close'] < (prev2['open'] + prev2['close']) / 2):
                    patterns.append(CandlePattern(
                        name="Evening Star",
                        direction="bearish",
                        strength=0.85,
                        description="Strong bearish reversal pattern"
                    ))
        
        return patterns
    
    def detect_flag_pattern(self, df: pd.DataFrame) -> Optional[ChartPattern]:
        """Detect bull/bear flags and pennants"""
        if len(df) < 30:
            return None
        
        recent = df.tail(30)
        
        # Look for strong preceding move (pole)
        first_10 = recent.head(10)
        last_20 = recent.tail(20)
        
        pole_move = (first_10['close'].iloc[-1] - first_10['close'].iloc[0]) / first_10['close'].iloc[0]
        
        if abs(pole_move) < 0.01:  # At least 1% move
            return None
        
        # Check for consolidation (flag)
        consolidation_high = last_20['high'].max()
        consolidation_low = last_20['low'].min()
        consolidation_range = (consolidation_high - consolidation_low) / consolidation_low
        
        if consolidation_range > abs(pole_move) * 0.5:  # Consolidation should be smaller than pole
            return None
        
        direction = "bullish" if pole_move > 0 else "bearish"
        pattern_name = "Bull Flag" if pole_move > 0 else "Bear Flag"
        
        return ChartPattern(
            name=pattern_name,
            direction=direction,
            strength=0.75,
            key_levels=[consolidation_high, consolidation_low],
            description=f"{pattern_name} pattern detected after {abs(pole_move)*100:.1f}% pole move"
        )
    
    def detect_channel(self, df: pd.DataFrame) -> Optional[ChartPattern]:
        """Detect price channels (parallel trendlines)"""
        if len(df) < 50:
            return None
        
        recent = df.tail(50)
        
        # Find swing highs and lows
        highs = recent['high'].values
        lows = recent['low'].values
        
        # Simple channel detection using linear regression
        x = np.arange(len(recent))
        
        # Upper channel (swing highs)
        high_slope, high_intercept = np.polyfit(x, highs, 1)
        
        # Lower channel (swing lows)  
        low_slope, low_intercept = np.polyfit(x, lows, 1)
        
        # Check if slopes are similar (parallel)
        slope_diff = abs(high_slope - low_slope)
        avg_slope = (high_slope + low_slope) / 2
        
        if slope_diff > abs(avg_slope) * 0.3:  # Too different, not a channel
            return None
        
        # Check if price respects the channel
        upper_line = high_slope * x + high_intercept
        lower_line = low_slope * x + low_intercept
        
        price_range = recent['high'].max() - recent['low'].min()
        upper_touch_pct = np.sum(highs >= upper_line - price_range * 0.05) / len(highs)
        lower_touch_pct = np.sum(lows <= lower_line + price_range * 0.05) / len(lows)
        
        if upper_touch_pct < 0.1 or lower_touch_pct < 0.1:
            return None
        
        direction = "bullish" if avg_slope > 0 else "bearish" if avg_slope < 0 else "sideways"
        channel_type = "Ascending" if avg_slope > 0.001 else "Descending" if avg_slope < -0.001 else "Horizontal"
        
        return ChartPattern(
            name=f"{channel_type} Channel",
            direction=direction,
            strength=0.7,
            key_levels=[upper_line[-1], lower_line[-1]],
            description=f"{channel_type} channel with {upper_touch_pct*100:.0f}% upper, {lower_touch_pct*100:.0f}% lower touches"
        )
    
    def find_support_resistance(self, df: pd.DataFrame, timeframe: str, num_levels: int = 5) -> List[SupportResistance]:
        """Find key support and resistance levels using pivot points"""
        if len(df) < 20:
            return []
        
        levels = []
        
        # Find local maxima and minima
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        # Simple pivot detection
        pivot_highs = []
        pivot_lows = []
        
        for i in range(2, len(df) - 2):
            # Pivot high
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                pivot_highs.append((i, highs[i]))
            # Pivot low
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                pivot_lows.append((i, lows[i]))
        
        # Cluster nearby levels
        def cluster_levels(pivots, level_type: str):
            if not pivots:
                return
            
            # Group by proximity (0.1% for forex)
            tolerance = closes[-1] * 0.001
            clusters = []
            current_cluster = [pivots[0]]
            
            for i in range(1, len(pivots)):
                if abs(pivots[i][1] - current_cluster[0][1]) < tolerance:
                    current_cluster.append(pivots[i])
                else:
                    clusters.append(current_cluster)
                    current_cluster = [pivots[i]]
            clusters.append(current_cluster)
            
            for cluster in clusters[:num_levels]:
                avg_price = sum(p[1] for p in cluster) / len(cluster)
                recency = len(df) - max(p[0] for p in cluster)
                strength = min(len(cluster) * 0.2 + 1 / (recency / 10 + 1), 1.0)
                
                levels.append(SupportResistance(
                    level=round(avg_price, 5),
                    type=level_type,
                    strength=round(strength, 2),
                    touches=len(cluster),
                    timeframe=timeframe
                ))
        
        cluster_levels(pivot_highs[-20:], "resistance")
        cluster_levels(pivot_lows[-20:], "support")
        
        # Sort by strength
        levels.sort(key=lambda x: x.strength, reverse=True)
        return levels[:num_levels]
    
    def analyze_timeframe(self, symbol: str, tf: TimeFrame, bars: int = 500) -> Optional[TimeFrameAnalysis]:
        """Complete analysis of a single timeframe"""
        df = self.fetch_data(symbol, tf.value, bars)
        if df is None or len(df) < 100:
            return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # Calculate all indicators
        indicators = IndicatorValues()
        
        # Moving Averages
        indicators.ma_20 = round(self.calculate_ma(df, 20).iloc[-1], 5)
        indicators.ma_50 = round(self.calculate_ma(df, 50).iloc[-1], 5)
        indicators.ma_200 = round(self.calculate_ma(df, 200).iloc[-1], 5) if len(df) >= 200 else None
        
        # RSI
        indicators.rsi_14 = round(self.calculate_rsi(df, 14).iloc[-1], 2)
        
        # MACD
        macd_line, signal_line, histogram = self.calculate_macd(df)
        indicators.macd_line = round(macd_line.iloc[-1], 5)
        indicators.macd_signal = round(signal_line.iloc[-1], 5)
        indicators.macd_histogram = round(histogram.iloc[-1], 5)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger(df)
        indicators.bb_upper = round(bb_upper.iloc[-1], 5)
        indicators.bb_middle = round(bb_middle.iloc[-1], 5)
        indicators.bb_lower = round(bb_lower.iloc[-1], 5)
        indicators.bb_width = round((bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_middle.iloc[-1], 4)
        
        # BB position (0 = at lower, 1 = at upper)
        bb_range = bb_upper.iloc[-1] - bb_lower.iloc[-1]
        indicators.bb_position = round((latest['close'] - bb_lower.iloc[-1]) / bb_range, 4) if bb_range > 0 else 0.5
        
        # ATR
        indicators.atr_14 = round(self.calculate_atr(df, 14).iloc[-1], 5)
        
        # ADX
        adx, plus_di, minus_di = self.calculate_adx(df, 14)
        indicators.adx_14 = round(adx.iloc[-1], 2)
        indicators.plus_di = round(plus_di.iloc[-1], 2)
        indicators.minus_di = round(minus_di.iloc[-1], 2)
        
        # Determine trend
        price = latest['close']
        ma_bullish = price > indicators.ma_20 > indicators.ma_50
        ma_bearish = price < indicators.ma_20 < indicators.ma_50
        
        adx_strong = indicators.adx_14 > 25 if indicators.adx_14 else False
        
        if ma_bullish:
            trend = "bullish"
            trend_strength = 0.7 + (0.2 if adx_strong else 0)
        elif ma_bearish:
            trend = "bearish"
            trend_strength = 0.7 + (0.2 if adx_strong else 0)
        else:
            trend = "sideways"
            trend_strength = 0.4
        
        # Detect patterns
        candle_patterns = self.detect_candle_patterns(df.tail(10))
        chart_patterns = []
        
        flag = self.detect_flag_pattern(df)
        if flag:
            chart_patterns.append(flag)
        
        channel = self.detect_channel(df)
        if channel:
            chart_patterns.append(channel)
        
        # Support/Resistance
        sr_levels = self.find_support_resistance(df, tf.name)
        
        # Key levels
        key_levels = {
            "day_high": round(df['high'].tail(24 if tf == TimeFrame.H1 else 1).max(), 5),
            "day_low": round(df['low'].tail(24 if tf == TimeFrame.H1 else 1).min(), 5),
            "week_high": round(df['high'].tail(120 if tf == TimeFrame.H1 else 5).max(), 5),
            "week_low": round(df['low'].tail(120 if tf == TimeFrame.H1 else 5).min(), 5),
        }
        
        # Volatility (ATR-based)
        volatility = round((indicators.atr_14 / price) * 100, 4) if indicators.atr_14 else 0
        
        # Generate summary
        summary_parts = []
        summary_parts.append(f"Trend: {trend} ({trend_strength:.0%})")
        if indicators.rsi_14:
            rsi_state = "oversold" if indicators.rsi_14 < 30 else "overbought" if indicators.rsi_14 > 70 else "neutral"
            summary_parts.append(f"RSI: {indicators.rsi_14:.1f} ({rsi_state})")
        if candle_patterns:
            summary_parts.append(f"Patterns: {', '.join([p.name for p in candle_patterns[:2]])}")
        
        analysis_summary = " | ".join(summary_parts)
        
        return TimeFrameAnalysis(
            symbol=symbol,
            timeframe=tf.name,
            timestamp=datetime.now().isoformat(),
            current_price=round(price, 5),
            open=round(latest['open'], 5),
            high=round(latest['high'], 5),
            low=round(latest['low'], 5),
            close=round(latest['close'], 5),
            volume=int(latest['tick_volume']),
            indicators=indicators,
            trend=trend,
            trend_strength=round(trend_strength, 2),
            candle_patterns=candle_patterns,
            chart_patterns=chart_patterns,
            support_resistance=sr_levels,
            key_levels=key_levels,
            volatility=volatility,
            analysis_summary=analysis_summary
        )
    
    def calculate_alignment_score(self, analyses: Dict[str, TimeFrameAnalysis]) -> float:
        """Calculate how well timeframes align"""
        if len(analyses) < 2:
            return 0.5
        
        trends = [a.trend for a in analyses.values()]
        bullish_count = sum(1 for t in trends if t == "bullish")
        bearish_count = sum(1 for t in trends if t == "bearish")
        
        max_aligned = max(bullish_count, bearish_count)
        return max_aligned / len(trends)
    
    def determine_overall_bias(self, analyses: Dict[str, TimeFrameAnalysis]) -> Tuple[str, float, str]:
        """Determine overall market bias and recommended direction"""
        weights = {"D1": 0.35, "H4": 0.30, "H1": 0.20, "M15": 0.15}
        
        bullish_score = 0
        bearish_score = 0
        total_weight = 0
        
        for tf_name, analysis in analyses.items():
            weight = weights.get(tf_name, 0.1)
            total_weight += weight
            
            if analysis.trend == "bullish":
                bullish_score += weight * analysis.trend_strength
            elif analysis.trend == "bearish":
                bearish_score += weight * analysis.trend_strength
        
        if total_weight == 0:
            return "neutral", 0.5, "NEUTRAL"
        
        bullish_score /= total_weight
        bearish_score /= total_weight
        
        if bullish_score > bearish_score * 1.2:
            return "bullish", bullish_score, "BUY"
        elif bearish_score > bullish_score * 1.2:
            return "bearish", bearish_score, "SELL"
        else:
            return "mixed", max(bullish_score, bearish_score), "NEUTRAL"
    
    def find_confluences(self, analyses: Dict[str, TimeFrameAnalysis]) -> List[str]:
        """Find confluences across timeframes"""
        confluences = []
        
        # Check if all timeframes agree on trend
        trends = [a.trend for a in analyses.values()]
        if all(t == "bullish" for t in trends):
            confluences.append("ALL_TIME_FRAMES_BULLISH")
        elif all(t == "bearish" for t in trends):
            confluences.append("ALL_TIME_FRAMES_BEARISH")
        
        # Check RSI alignment
        rsis = [(tf, a.indicators.rsi_14) for tf, a in analyses.items() if a.indicators.rsi_14]
        oversold_tfs = [tf for tf, rsi in rsis if rsi and rsi < 30]
        overbought_tfs = [tf for tf, rsi in rsis if rsi and rsi > 70]
        
        if len(oversold_tfs) >= 2:
            confluences.append(f"MULTI_TIME_FRAME_OVERSOLD ({', '.join(oversold_tfs)})")
        if len(overbought_tfs) >= 2:
            confluences.append(f"MULTI_TIME_FRAME_OVERBOUGHT ({', '.join(overbought_tfs)})")
        
        # Check MACD alignment
        macd_bullish = [tf for tf, a in analyses.items() if a.indicators.macd_histogram and a.indicators.macd_histogram > 0]
        macd_bearish = [tf for tf, a in analyses.items() if a.indicators.macd_histogram and a.indicators.macd_histogram < 0]
        
        if len(macd_bullish) >= 3:
            confluences.append("MACD_BULLISH_ALIGNMENT")
        if len(macd_bearish) >= 3:
            confluences.append("MACD_BEARISH_ALIGNMENT")
        
        # Check for price at key levels on multiple timeframes
        for tf, analysis in analyses.items():
            if analysis.indicators.bb_position is not None:
                if analysis.indicators.bb_position < 0.05:
                    confluences.append(f"PRICE_AT_LOWER_BB ({tf})")
                elif analysis.indicators.bb_position > 0.95:
                    confluences.append(f"PRICE_AT_UPPER_BB ({tf})")
        
        return confluences
    
    def analyze_symbol(self, symbol: str) -> Optional[MultiTimeframeAnalysis]:
        """Complete multi-timeframe analysis for a symbol"""
        print(f"\n{'='*60}")
        print(f"Analyzing {symbol}...")
        print(f"{'='*60}")
        
        timeframes = {
            "D1": TimeFrame.D1,
            "H4": TimeFrame.H4,
            "H1": TimeFrame.H1,
            "M15": TimeFrame.M15
        }
        
        analyses = {}
        for tf_name, tf_enum in timeframes.items():
            print(f"  [{tf_name}] Fetching data...", end=" ")
            analysis = self.analyze_timeframe(symbol, tf_enum)
            if analysis:
                analyses[tf_name] = analysis
                print(f"OK | {analysis.trend.upper()}")
            else:
                print(f"FAIL")
        
        if not analyses:
            print(f"[ERROR] No data available for {symbol}")
            return None
        
        # Calculate aggregated metrics
        alignment_score = self.calculate_alignment_score(analyses)
        bias, confidence, direction = self.determine_overall_bias(analyses)
        confluences = self.find_confluences(analyses)
        
        # Determine invalidation level (key S/R level against bias)
        invalidation = 0
        if direction == "BUY":
            # Find strongest support below price
            for tf in ["D1", "H4", "H1"]:
                if tf in analyses:
                    supports = [sr.level for sr in analyses[tf].support_resistance if sr.type == "support"]
                    if supports:
                        invalidation = min(supports)
                        break
        elif direction == "SELL":
            # Find strongest resistance above price
            for tf in ["D1", "H4", "H1"]:
                if tf in analyses:
                    resistances = [sr.level for sr in analyses[tf].support_resistance if sr.type == "resistance"]
                    if resistances:
                        invalidation = max(resistances)
                        break
        
        result = MultiTimeframeAnalysis(
            symbol=symbol,
            timestamp=datetime.now().isoformat(),
            timeframes=analyses,
            overall_bias=bias,
            confidence=round(confidence, 4),
            alignment_score=round(alignment_score, 4),
            key_confluences=confluences,
            recommended_direction=direction,
            invalidation_level=round(invalidation, 5) if invalidation else 0
        )
        
        print(f"\n  OVERALL: {bias.upper()} | Confidence: {confidence:.1%} | Alignment: {alignment_score:.1%}")
        print(f"  Direction: {direction}")
        print(f"  Confluences: {len(confluences)}")
        
        return result
    
    def to_dict(self, obj):
        """Convert dataclass/frozen dataclass to dict recursively"""
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for key, value in asdict(obj).items():
                result[key] = self.to_dict(value)
            return result
        elif isinstance(obj, (list, tuple)):
            return [self.to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self.to_dict(value) for key, value in obj.items()}
        elif isinstance(obj, Enum):
            return obj.name
        else:
            return obj
    
    def save_analysis(self, analysis: MultiTimeframeAnalysis, output_dir: Optional[Path] = None):
        """Save analysis to JSON file"""
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "output"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{analysis.symbol}_{timestamp}_technical.json"
        filepath = output_dir / filename
        
        data = self.to_dict(analysis)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"  [SAVED] {filepath}")
        return filepath
    
    def scan_and_save_all(self):
        """Scan all symbols and save results - interface for orchestrator"""
        if not self.connected:
            if not self.connect():
                print("[ERROR] Could not connect to MT5")
                return []
        
        all_results = []
        for symbol in self.symbols:
            result = self.analyze_symbol(symbol)
            if result:
                filepath = self.save_analysis(result)
                all_results.append({
                    "symbol": symbol,
                    "bias": result.overall_bias,
                    "direction": result.recommended_direction,
                    "confidence": result.confidence,
                    "file": str(filepath)
                })
        
        self.results = all_results
        return all_results


def main():
    """Main execution - test on EURUSD, GBPUSD, USDJPY"""
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    
    analyzer = TechnicalAnalyzer()
    
    if not analyzer.connect():
        print("[FATAL] Could not connect to MT5")
        sys.exit(1)
    
    try:
        all_results = []
        
        for symbol in symbols:
            result = analyzer.analyze_symbol(symbol)
            if result:
                filepath = analyzer.save_analysis(result)
                all_results.append({
                    "symbol": symbol,
                    "bias": result.overall_bias,
                    "direction": result.recommended_direction,
                    "confidence": result.confidence,
                    "alignment": result.alignment_score,
                    "file": str(filepath)
                })
        
        # Summary report
        print(f"\n{'='*60}")
        print("ANALYSIS SUMMARY")
        print(f"{'='*60}")
        for r in all_results:
            print(f"  {r['symbol']:8} | {r['direction']:6} | Conf: {r['confidence']:.1%} | Align: {r['alignment']:.1%}")
        
        # Save summary
        output_dir = Path(__file__).parent.parent / "output"
        summary_file = output_dir / f"technical_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": all_results
            }, f, indent=2)
        
        print(f"\n[OK] Summary saved to {summary_file}")
        
    finally:
        analyzer.disconnect()


if __name__ == "__main__":
    main()
