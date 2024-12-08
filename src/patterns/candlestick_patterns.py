import numpy as np
import pandas as pd
from typing import Tuple

class CandlestickPatterns:
    @staticmethod
    def is_engulfing(df: pd.DataFrame, idx: int) -> Tuple[bool, bool]:
        """
        Check for bullish and bearish engulfing patterns
        Returns: (is_bullish_engulfing, is_bearish_engulfing)
        """
        if idx < 1:
            return False, False
            
        curr_open, curr_close = df['Open'].iloc[idx], df['Close'].iloc[idx]
        prev_open, prev_close = df['Open'].iloc[idx-1], df['Close'].iloc[idx-1]
        
        bullish_engulfing = (
            prev_close < prev_open and  # Previous red candle
            curr_close > curr_open and  # Current green candle
            curr_open < prev_close and  # Current opens below previous close
            curr_close > prev_open      # Current closes above previous open
        )
        
        bearish_engulfing = (
            prev_close > prev_open and  # Previous green candle
            curr_close < curr_open and  # Current red candle
            curr_open > prev_close and  # Current opens above previous close
            curr_close < prev_open      # Current closes below previous open
        )
        
        return bullish_engulfing, bearish_engulfing
    
    @staticmethod
    def is_doji(df: pd.DataFrame, idx: int, threshold: float = 0.1) -> bool:
        """Check for doji pattern"""
        if idx < 0:
            return False
            
        body_size = abs(df['Close'].iloc[idx] - df['Open'].iloc[idx])
        high_low_range = df['High'].iloc[idx] - df['Low'].iloc[idx]
        
        return body_size <= (high_low_range * threshold)
    
    @staticmethod
    def is_hammer(df: pd.DataFrame, idx: int) -> bool:
        """Check for hammer pattern"""
        if idx < 0:
            return False
            
        body_size = abs(df['Close'].iloc[idx] - df['Open'].iloc[idx])
        lower_wick = min(df['Open'].iloc[idx], df['Close'].iloc[idx]) - df['Low'].iloc[idx]
        upper_wick = df['High'].iloc[idx] - max(df['Open'].iloc[idx], df['Close'].iloc[idx])
        
        return (lower_wick > (2 * body_size) and  # Long lower wick
                upper_wick < (0.1 * body_size))    # Very small upper wick
    
    @staticmethod
    def is_shooting_star(df: pd.DataFrame, idx: int) -> bool:
        """Check for shooting star pattern"""
        if idx < 0:
            return False
            
        body_size = abs(df['Close'].iloc[idx] - df['Open'].iloc[idx])
        lower_wick = min(df['Open'].iloc[idx], df['Close'].iloc[idx]) - df['Low'].iloc[idx]
        upper_wick = df['High'].iloc[idx] - max(df['Open'].iloc[idx], df['Close'].iloc[idx])
        
        return (upper_wick > (2 * body_size) and  # Long upper wick
                lower_wick < (0.1 * body_size))    # Very small lower wick
    
    @staticmethod
    def is_marubozu(df: pd.DataFrame, idx: int, threshold: float = 0.1) -> Tuple[bool, bool]:
        """
        Check for marubozu (strong trend candle with little to no wicks)
        Returns: (is_bullish_marubozu, is_bearish_marubozu)
        """
        if idx < 0:
            return False, False
            
        open_price = df['Open'].iloc[idx]
        close_price = df['Close'].iloc[idx]
        high_price = df['High'].iloc[idx]
        low_price = df['Low'].iloc[idx]
        
        body_size = abs(close_price - open_price)
        total_range = high_price - low_price
        
        if body_size < (total_range * 0.9):  # Body should be at least 90% of total range
            return False, False
            
        bullish_marubozu = (
            close_price > open_price and
            (high_price - close_price) <= (threshold * body_size) and
            (open_price - low_price) <= (threshold * body_size)
        )
        
        bearish_marubozu = (
            close_price < open_price and
            (high_price - open_price) <= (threshold * body_size) and
            (close_price - low_price) <= (threshold * body_size)
        )
        
        return bullish_marubozu, bearish_marubozu
