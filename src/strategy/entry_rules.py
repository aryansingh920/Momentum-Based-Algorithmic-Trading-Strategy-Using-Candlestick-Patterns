from typing import Tuple, Dict
import pandas as pd
from ..patterns.candlestick_patterns import CandlestickPatterns
from ..patterns.momentum_patterns import MomentumPatterns
from ..indicators.momentum_indicators import MomentumIndicators
from ..indicators.volatility_indicators import VolatilityIndicators


class EntryRules:
    def __init__(self,
                 candlestick_patterns: CandlestickPatterns,
                 momentum_patterns: MomentumPatterns,
                 momentum_indicators: MomentumIndicators,
                 volatility_indicators: VolatilityIndicators):
        self.candlestick_patterns = candlestick_patterns
        self.momentum_patterns = momentum_patterns
        self.momentum_indicators = momentum_indicators
        self.volatility_indicators = volatility_indicators

    def check_entry_signals(self, df: pd.DataFrame, idx: int) -> Tuple[bool, bool, Dict]:
        """
        Check all entry conditions
        Returns: (bullish_entry, bearish_entry, signal_details)
        """
        if idx < 20:  # Need sufficient history
            return False, False, {}

        signal_details = {}

        # Check candlestick patterns
        bull_engulf, bear_engulf = self.candlestick_patterns.is_engulfing(
            df, idx)
        signal_details['engulfing'] = {
            'bullish': bull_engulf, 'bearish': bear_engulf}

        is_doji = self.candlestick_patterns.is_doji(df, idx)
        is_hammer = self.candlestick_patterns.is_hammer(df, idx)
        is_shooting_star = self.candlestick_patterns.is_shooting_star(df, idx)
        bull_marubozu, bear_marubozu = self.candlestick_patterns.is_marubozu(
            df, idx)

        signal_details['candlestick'] = {
            'doji': is_doji,
            'hammer': is_hammer,
            'shooting_star': is_shooting_star,
            'marubozu': {'bullish': bull_marubozu, 'bearish': bear_marubozu}
        }

        # Check momentum patterns
        bull_breakout, bear_breakout = self.momentum_patterns.is_breakout_candle(
            df, idx)
        momentum_confirmed = self.momentum_patterns.is_momentum_confirmed(
            df, idx)
        momentum_score = self.momentum_patterns.calculate_momentum_score(
            df, idx)

        signal_details['momentum'] = {
            'breakout': {'bullish': bull_breakout, 'bearish': bear_breakout},
            'confirmed': momentum_confirmed,
            'score': momentum_score
        }

        # Get indicator signals
        indicator_signals = self.momentum_indicators.get_momentum_signals(
            df, idx)
        trend_strength = self.momentum_indicators.get_trend_strength(df, idx)

        signal_details['indicators'] = {
            **indicator_signals,
            'trend_strength': trend_strength
        }

        # Combine signals for final entry decision
        bullish_entry = (
            (bull_engulf or (is_doji and momentum_score > 0) or
             is_hammer or bull_marubozu or bull_breakout) and
            momentum_confirmed and
            trend_strength > 0.3 and
            not indicator_signals['rsi_overbought']
        )

        bearish_entry = (
            (bear_engulf or (is_doji and momentum_score < 0) or
             is_shooting_star or bear_marubozu or bear_breakout) and
            momentum_confirmed and
            trend_strength < -0.3 and
            not indicator_signals['rsi_oversold']
        )

        return bullish_entry, bearish_entry, signal_details

    def calculate_position_size(self, df: pd.DataFrame, idx: int,
                                base_position: float = 1.0) -> float:
        """Calculate position size based on volatility and momentum strength"""
        momentum_score = abs(
            self.momentum_patterns.calculate_momentum_score(df, idx))
        momentum_factor = 0.5 + (momentum_score * 0.5)  # Scale 0.5 to 1.0

        vol_adjusted_size = self.volatility_indicators.get_volatility_adjusted_position_size(
            df, idx, base_position
        )

        return vol_adjusted_size * momentum_factor
