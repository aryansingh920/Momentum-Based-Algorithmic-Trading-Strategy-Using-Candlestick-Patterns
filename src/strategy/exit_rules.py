from typing import Tuple, Dict
import pandas as pd
from ..patterns.candlestick_patterns import CandlestickPatterns
from ..patterns.momentum_patterns import MomentumPatterns
from ..indicators.momentum_indicators import MomentumIndicators
from ..indicators.volatility_indicators import VolatilityIndicators


class ExitRules:
    def __init__(self,
                 candlestick_patterns: CandlestickPatterns,
                 momentum_patterns: MomentumPatterns,
                 momentum_indicators: MomentumIndicators,
                 volatility_indicators: VolatilityIndicators):
        self.candlestick_patterns = candlestick_patterns
        self.momentum_patterns = momentum_patterns
        self.momentum_indicators = momentum_indicators
        self.volatility_indicators = volatility_indicators

    def check_exit_signals(self, df: pd.DataFrame, idx: int,
                           position_type: str) -> Tuple[bool, Dict]:
        """
        Check all exit conditions
        position_type: 'long' or 'short'
        Returns: (should_exit, exit_details)
        """
        if idx < 1:
            return False, {}

        exit_details = {}

        # Check reversal patterns
        bull_engulf, bear_engulf = self.candlestick_patterns.is_engulfing(
            df, idx)
        is_shooting_star = self.candlestick_patterns.is_shooting_star(df, idx)
        is_hammer = self.candlestick_patterns.is_hammer(df, idx)

        exit_details['reversal_patterns'] = {
            'engulfing': {'bullish': bull_engulf, 'bearish': bear_engulf},
            'shooting_star': is_shooting_star,
            'hammer': is_hammer
        }

        # Check momentum
        momentum_score = self.momentum_patterns.calculate_momentum_score(
            df, idx)
        trend_strength = self.momentum_indicators.get_trend_strength(df, idx)

        exit_details['momentum'] = {
            'score': momentum_score,
            'trend_strength': trend_strength
        }

        # Get indicator signals
        indicator_signals = self.momentum_indicators.get_momentum_signals(
            df, idx)
        exit_details['indicators'] = indicator_signals

        # Determine exit based on position type
        if position_type == 'long':
            should_exit = (
                bear_engulf or
                is_shooting_star or
                (momentum_score < -0.3 and trend_strength < 0) or
                indicator_signals['macd_bearish_cross'] or
                indicator_signals['rsi_overbought']
            )
        else:  # short position
            should_exit = (
                bull_engulf or
                is_hammer or
                (momentum_score > 0.3 and trend_strength > 0) or
                indicator_signals['macd_bullish_cross'] or
                indicator_signals['rsi_oversold']
            )

        return should_exit, exit_details

    def calculate_trailing_stop(self, df: pd.DataFrame, idx: int,
                                position_type: str, entry_price: float) -> float:
        """Calculate trailing stop level based on ATR and price action"""
        if idx < 1:
            return entry_price

        stop_distance, _ = self.volatility_indicators.get_dynamic_stops(
            df, idx)
        current_price = df['Close'].iloc[idx]

        if position_type == 'long':
            trail_level = current_price - \
                (stop_distance * 1.5)  # Wider trailing stop
            # Don't go below entry - 1%
            return max(trail_level, entry_price * 0.99)
        else:
            trail_level = current_price + (stop_distance * 1.5)
            # Don't go above entry + 1%
            return min(trail_level, entry_price * 1.01)

    def should_move_stop_to_breakeven(self, df: pd.DataFrame, idx: int,
                                      position_type: str, entry_price: float) -> bool:
        """Determine if stop loss should be moved to breakeven"""
        if idx < 1:
            return False

        current_price = df['Close'].iloc[idx]
        _, take_profit_distance = self.volatility_indicators.get_dynamic_stops(
            df, idx)

        if position_type == 'long':
            profit_target = entry_price + take_profit_distance
            return current_price >= (entry_price + (take_profit_distance * 0.5))
        else:
            profit_target = entry_price - take_profit_distance
            return current_price <= (entry_price - (take_profit_distance * 0.5))
