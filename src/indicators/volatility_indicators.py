import numpy as np
import pandas as pd
import talib as ta
from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class VolatilityParams:
    atr_period: int = 14
    volatility_lookback: int = 20
    std_dev_period: int = 20
    bollinger_bands_std: float = 2.0
    minimum_atr_value: float = 0.001  # Minimum ATR value to prevent division by zero


class VolatilityIndicators:
    def __init__(self, params: VolatilityParams = VolatilityParams()):
        self.params = params

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all volatility indicators"""
        df = df.copy()

        # Average True Range (ATR)
        df['ATR'] = ta.ATR(
            df['High'],
            df['Low'],
            df['Close'],
            timeperiod=self.params.atr_period
        )

        # Normalize ATR by price
        df['ATR_Pct'] = (df['ATR'] / df['Close']) * 100

        # Historical volatility (standard deviation of returns)
        returns = df['Close'].pct_change()
        df['Historical_Volatility'] = returns.rolling(
            window=self.params.volatility_lookback
        ).std() * np.sqrt(252)  # Annualize volatility

        # Bollinger Bands based on ATR
        df['ATR_MA'] = df['ATR'].rolling(
            window=self.params.std_dev_period).mean()
        df['ATR_Std'] = df['ATR'].rolling(
            window=self.params.std_dev_period).std()
        df['ATR_Upper'] = df['ATR_MA'] + \
            (df['ATR_Std'] * self.params.bollinger_bands_std)
        df['ATR_Lower'] = df['ATR_MA'] - \
            (df['ATR_Std'] * self.params.bollinger_bands_std)

        # Volatility regime (0: low, 1: normal, 2: high)
        df['Volatility_Regime'] = self._calculate_volatility_regime(df)

        # Rate of change of ATR
        df['ATR_ROC'] = df['ATR'].pct_change(periods=5) * 100

        return df

    def _calculate_volatility_regime(self, df: pd.DataFrame) -> pd.Series:
        """Determine volatility regime based on ATR"""
        atr_percentile = df['ATR'].rolling(window=100).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1]
        )

        regime = pd.Series(index=df.index, data=1)  # Default to normal regime
        regime[atr_percentile <= 0.25] = 0  # Low volatility
        regime[atr_percentile >= 0.75] = 2  # High volatility

        return regime

    def get_dynamic_stops(self, df: pd.DataFrame, idx: int,
                          base_multiplier: float = 2.0) -> Tuple[float, float]:
        """
        Calculate dynamic stop loss and take profit distances based on ATR
        Adjusts distances based on volatility regime
        
        Returns: (stop_distance, take_profit_distance)
        """
        if idx < 1:
            return None, None

        # Get current ATR and regime
        current_atr = max(df['ATR'].iloc[idx], self.params.minimum_atr_value)
        regime = df['Volatility_Regime'].iloc[idx]

        # Adjust multiplier based on regime
        regime_multipliers = {
            0: 1.5,  # Tighter stops in low volatility
            1: 1.0,  # Normal volatility
            2: 0.75  # Tighter stops in high volatility
        }

        adjusted_multiplier = base_multiplier * regime_multipliers[regime]

        stop_distance = current_atr * adjusted_multiplier
        take_profit_distance = stop_distance * 2  # 1:2 risk-reward ratio

        return stop_distance, take_profit_distance

    def get_volatility_adjusted_position_size(self, df: pd.DataFrame, idx: int,
                                              base_position: float = 1.0,
                                              min_size: float = 0.25,
                                              max_size: float = 2.0) -> float:
        """
        Calculate position size inversely proportional to volatility
        Includes regime-based adjustments
        """
        if idx < self.params.volatility_lookback:
            return base_position

        current_vol = df['Historical_Volatility'].iloc[idx]
        avg_vol = df['Historical_Volatility'].iloc[idx -
                                                   self.params.volatility_lookback:idx].mean()

        # Base adjustment based on volatility ratio
        # Prevent division by zero
        vol_ratio = avg_vol / max(current_vol, 0.001)

        # Additional adjustment based on regime
        regime = df['Volatility_Regime'].iloc[idx]
        regime_adjustments = {
            0: 1.2,   # Increase size in low volatility
            1: 1.0,   # Normal volatility
            2: 0.8    # Reduce size in high volatility
        }

        adjusted_position = base_position * \
            vol_ratio * regime_adjustments[regime]

        # Ensure position size stays within bounds
        return max(min(adjusted_position, max_size), min_size)

    def is_volatility_breakout(self, df: pd.DataFrame, idx: int,
                               lookback: int = 20,
                               threshold: float = 1.5) -> bool:
        """
        Detect significant volatility breakouts
        Returns True if current volatility is significantly above recent average
        """
        if idx < lookback:
            return False

        current_atr = df['ATR'].iloc[idx]
        avg_atr = df['ATR'].iloc[idx-lookback:idx].mean()

        return current_atr > (avg_atr * threshold)

    def get_trend_volatility_signal(self, df: pd.DataFrame, idx: int,
                                    trend_window: int = 20) -> Optional[str]:
        """
        Generate trading signal based on trend and volatility conditions
        Returns: 'long', 'short', or None
        """
        if idx < trend_window:
            return None

        # Calculate price trend
        price_sma = df['Close'].rolling(window=trend_window).mean()
        trend_direction = 1 if df['Close'].iloc[idx] > price_sma.iloc[idx] else -1

        # Check if volatility is favorable for trading
        regime = df['Volatility_Regime'].iloc[idx]
        vol_breakout = self.is_volatility_breakout(df, idx)

        # Generate signal based on conditions
        if regime != 2 and not vol_breakout:  # Avoid extreme volatility
            if trend_direction == 1 and df['ATR_ROC'].iloc[idx] > 0:
                return 'long'
            elif trend_direction == -1 and df['ATR_ROC'].iloc[idx] > 0:
                return 'short'

        return None

    def get_volatility_summary(self, df: pd.DataFrame, idx: int) -> dict:
        """Generate summary of current volatility conditions"""
        if idx < self.params.volatility_lookback:
            return {}

        return {
            'current_atr': df['ATR'].iloc[idx],
            'atr_percentile': df['ATR'].iloc[idx-100:idx].rank(pct=True).iloc[-1],
            'volatility_regime': df['Volatility_Regime'].iloc[idx],
            'historical_volatility': df['Historical_Volatility'].iloc[idx],
            'atr_trend': 'Increasing' if df['ATR_ROC'].iloc[idx] > 0 else 'Decreasing',
            'is_breakout': self.is_volatility_breakout(df, idx)
        }
