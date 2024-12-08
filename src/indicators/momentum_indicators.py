import numpy as np
import pandas as pd
import talib as ta
from dataclasses import dataclass
from typing import Tuple


@dataclass
class IndicatorParams:
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_period: int = 20
    bb_std: float = 2.0


class MomentumIndicators:
    def __init__(self, params: IndicatorParams = IndicatorParams()):
        self.params = params

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all momentum indicators"""
        df = df.copy()

        # RSI
        df['RSI'] = ta.RSI(df['Close'], timeperiod=self.params.rsi_period)

        # MACD
        macd, signal, hist = ta.MACD(
            df['Close'],
            fastperiod=self.params.macd_fast,
            slowperiod=self.params.macd_slow,
            signalperiod=self.params.macd_signal
        )
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist

        # Bollinger Bands
        upper, middle, lower = ta.BBANDS(
            df['Close'],
            timeperiod=self.params.bb_period,
            nbdevup=self.params.bb_std,
            nbdevdn=self.params.bb_std
        )
        df['BB_Upper'] = upper
        df['BB_Middle'] = middle
        df['BB_Lower'] = lower

        return df

    def get_momentum_signals(self, df: pd.DataFrame, idx: int) -> dict:
        """Get momentum signals from indicators"""
        signals = {
            'rsi_overbought': False,
            'rsi_oversold': False,
            'macd_bullish_cross': False,
            'macd_bearish_cross': False,
            'bb_upper_break': False,
            'bb_lower_break': False
        }

        if idx < 1:
            return signals

        # RSI signals
        current_rsi = df['RSI'].iloc[idx]
        signals['rsi_overbought'] = current_rsi > 70
        signals['rsi_oversold'] = current_rsi < 30

        # MACD crossover signals
        prev_hist = df['MACD_Hist'].iloc[idx-1]
        curr_hist = df['MACD_Hist'].iloc[idx]
        signals['macd_bullish_cross'] = prev_hist < 0 and curr_hist > 0
        signals['macd_bearish_cross'] = prev_hist > 0 and curr_hist < 0

        # Bollinger Band breakouts
        close = df['Close'].iloc[idx]
        signals['bb_upper_break'] = close > df['BB_Upper'].iloc[idx]
        signals['bb_lower_break'] = close < df['BB_Lower'].iloc[idx]

        return signals

    @staticmethod
    def get_trend_strength(df: pd.DataFrame, idx: int, window: int = 50) -> float:
        """
        Calculate trend strength (-1 to 1)
        Positive values indicate uptrend, negative values indicate downtrend
        """
        if idx < window:
            return 0.0

        # Calculate linear regression slope
        prices = df['Close'].iloc[idx-window:idx+1]
        x = np.arange(len(prices))
        slope, _ = np.polyfit(x, prices, 1)

        # Normalize slope to -1 to 1 range
        # Adjust multiplier for sensitivity
        normalized_slope = np.tanh(slope * 100)

        return normalized_slope
    
    import numpy as np


@dataclass
class VolatilityParams:
    atr_period: int = 14
    volatility_lookback: int = 20


class VolatilityIndicators:
    def __init__(self, params: VolatilityParams = VolatilityParams()):
        self.params = params

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all volatility indicators"""
        df = df.copy()

        # ATR
        df['ATR'] = ta.ATR(
            df['High'],
            df['Low'],
            df['Close'],
            timeperiod=self.params.atr_period
        )

        # Historical volatility (standard deviation of returns)
        returns = df['Close'].pct_change()
        df['Historical_Volatility'] = returns.rolling(
            window=self.params.volatility_lookback
        ).std() * np.sqrt(252)  # Annualized

        return df

    def get_dynamic_stops(self, df: pd.DataFrame, idx: int, multiplier: float = 2.0) -> tuple:
        """Calculate dynamic stop loss and take profit levels based on ATR"""
        if idx < 1:
            return None, None

        current_price = df['Close'].iloc[idx]
        current_atr = df['ATR'].iloc[idx]

        stop_distance = current_atr * multiplier
        take_profit_distance = current_atr * multiplier * 2  # 1:2 risk-reward ratio

        return stop_distance, take_profit_distance

    def is_volatility_breakout(self, df: pd.DataFrame, idx: int, threshold: float = 1.5) -> bool:
        """Check if current volatility is significantly above average"""
        if idx < self.params.volatility_lookback:
            return False

        current_vol = df['Historical_Volatility'].iloc[idx]
        avg_vol = df['Historical_Volatility'].iloc[idx -
                                                   self.params.volatility_lookback:idx].mean()

        return current_vol > (avg_vol * threshold)

    def get_volatility_adjusted_position_size(self, df: pd.DataFrame, idx: int,
                                              base_position: float = 1.0) -> float:
        """Calculate position size inversely proportional to volatility"""
        if idx < self.params.volatility_lookback:
            return base_position

        current_vol = df['Historical_Volatility'].iloc[idx]
        avg_vol = df['Historical_Volatility'].iloc[idx -
                                                   self.params.volatility_lookback:idx].mean()

        vol_ratio = avg_vol / current_vol
        adjusted_position = base_position * \
            min(max(vol_ratio, 0.5), 2.0)  # Limit adjustment range

        return adjusted_position
