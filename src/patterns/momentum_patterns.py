import numpy as np
import pandas as pd
from typing import Tuple


class MomentumPatterns:
    @staticmethod
    def is_breakout_candle(df: pd.DataFrame, idx: int, lookback: int = 20) -> Tuple[bool, bool]:
        """
        Identify breakout candles from consolidation
        Returns: (is_bullish_breakout, is_bearish_breakout)
        """
        if idx < lookback:
            return False, False

        # Calculate average candle size over lookback period
        candle_sizes = abs(
            df['Close'].iloc[idx-lookback:idx] - df['Open'].iloc[idx-lookback:idx])
        avg_size = candle_sizes.mean()

        current_size = abs(df['Close'].iloc[idx] - df['Open'].iloc[idx])
        is_large_candle = current_size > (
            2 * avg_size)  # Candle is 2x average size

        # Calculate price range during lookback period
        lookback_high = df['High'].iloc[idx-lookback:idx].max()
        lookback_low = df['Low'].iloc[idx-lookback:idx].min()
        consolidation_range = lookback_high - lookback_low

        # Check if price was in consolidation (range < 20% of price)
        avg_price = df['Close'].iloc[idx-lookback:idx].mean()
        is_consolidation = consolidation_range < (0.2 * avg_price)

        if not (is_large_candle and is_consolidation):
            return False, False

        # Determine breakout direction
        bullish_breakout = (
            df['Close'].iloc[idx] > df['Open'].iloc[idx] and  # Green candle
            # Closes above consolidation
            df['Close'].iloc[idx] > lookback_high
        )

        bearish_breakout = (
            df['Close'].iloc[idx] < df['Open'].iloc[idx] and  # Red candle
            # Closes below consolidation
            df['Close'].iloc[idx] < lookback_low
        )

        return bullish_breakout, bearish_breakout

    @staticmethod
    def is_momentum_confirmed(df: pd.DataFrame, idx: int, volume_threshold: float = 1.5) -> bool:
        """Check if momentum is confirmed by volume"""
        if idx < 20:  # Need some history for volume average
            return False

        # Calculate average volume
        avg_volume = df['Volume'].iloc[idx-20:idx].mean()
        current_volume = df['Volume'].iloc[idx]

        # Volume should be above threshold
        return current_volume > (volume_threshold * avg_volume)

    @staticmethod
    def calculate_momentum_score(df: pd.DataFrame, idx: int) -> float:
        """
        Calculate a momentum score (-1 to 1) based on recent price action
        Positive score indicates bullish momentum, negative indicates bearish
        """
        if idx < 20:
            return 0.0

        # Calculate short-term momentum (last 5 candles)
        short_term_return = (
            df['Close'].iloc[idx] - df['Close'].iloc[idx-5]) / df['Close'].iloc[idx-5]

        # Calculate medium-term momentum (last 20 candles)
        medium_term_return = (
            df['Close'].iloc[idx] - df['Close'].iloc[idx-20]) / df['Close'].iloc[idx-20]

        # Combine both timeframes with more weight on short-term
        momentum_score = (0.7 * short_term_return + 0.3 * medium_term_return)

        # Normalize to -1 to 1 range
        return max(min(momentum_score, 1.0), -1.0)
