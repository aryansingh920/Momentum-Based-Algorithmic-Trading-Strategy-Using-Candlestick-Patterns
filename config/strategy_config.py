from dataclasses import dataclass
from typing import Optional


@dataclass
class IndicatorConfig:
    # RSI settings
    rsi_period: int = 14
    rsi_overbought: float = 70
    rsi_oversold: float = 30

    # MACD settings
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    # Bollinger Bands settings
    bb_period: int = 20
    bb_std: float = 2.0

    # ATR settings
    atr_period: int = 14
    atr_multiplier: float = 2.0


@dataclass
class PatternConfig:
    # Candlestick pattern thresholds
    doji_threshold: float = 0.1
    engulfing_body_ratio: float = 1.2
    hammer_body_ratio: float = 0.3

    # Momentum pattern settings
    breakout_lookback: int = 20
    volume_threshold: float = 1.5
    consolidation_threshold: float = 0.2


@dataclass
class RiskConfig:
    # Position sizing
    initial_capital: float = 100000
    position_size: float = 0.1  # 10% of capital per trade
    max_position_size: float = 0.2

    # Risk management
    stop_loss_atr: float = 2.0
    take_profit_atr: float = 4.0  # 1:2 risk-reward ratio
    # Move to breakeven after 50% target reached
    trailing_stop_activation: float = 0.5
    max_trades_per_day: int = 3

    # Portfolio limits
    max_correlation: float = 0.7
    max_sector_exposure: float = 0.3


@dataclass
class BacktestConfig:
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    symbols: list = None

    # Backtest settings
    commission_rate: float = 0.001  # 0.1%
    slippage: float = 0.001  # 0.1%
    enable_fractional_shares: bool = True

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ['SPY']  # Default to S&P 500 ETF


@dataclass
class StrategyConfig:
    indicators: IndicatorConfig = IndicatorConfig()
    patterns: PatternConfig = PatternConfig()
    risk: RiskConfig = RiskConfig()
    backtest: BacktestConfig = BacktestConfig()

    # Strategy-specific settings
    require_volume_confirmation: bool = True
    min_trend_strength: float = 0.3
    enable_short_selling: bool = True
    trade_direction: str = 'both'  # 'long', 'short', or 'both'

    def validate(self):
        """Validate configuration parameters"""
        assert 0 < self.risk.position_size <= self.risk.max_position_size, \
            "Position size must be positive and not exceed max position size"

        assert self.risk.stop_loss_atr > 0, \
            "Stop loss ATR multiplier must be positive"

        assert self.risk.take_profit_atr > self.risk.stop_loss_atr, \
            "Take profit must be greater than stop loss"

        assert self.trade_direction in ['long', 'short', 'both'], \
            "Trade direction must be 'long', 'short', or 'both'"

        # Add more validation as needed
        return True


# Default configuration
DEFAULT_CONFIG = StrategyConfig()
