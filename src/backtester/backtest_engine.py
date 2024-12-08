import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from ..strategy.entry_rules import EntryRules
from ..strategy.exit_rules import ExitRules


@dataclass
class Position:
    type: str  # 'long' or 'short'
    entry_price: float
    entry_time: pd.Timestamp
    size: float
    stop_loss: float
    take_profit: float
    trailing_stop: float
    trade_id: int


class BacktestEngine:
    def __init__(self,
                 entry_rules: EntryRules,
                 exit_rules: ExitRules,
                 initial_capital: float = 100000,
                 position_size: float = 0.1):
        self.entry_rules = entry_rules
        self.exit_rules = exit_rules
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.reset()

    def reset(self):
        """Reset backtest state"""
        self.equity = self.initial_capital
        self.current_position: Optional[Position] = None
        self.trades: List[Dict] = []
        self.equity_curve = []
        self.trade_count = 0

    def run(self, df: pd.DataFrame) -> Dict:
        """Run backtest on historical data"""
        self.reset()
        results = []

        for idx in range(len(df)):
            equity_snapshot = self.process_bar(df, idx)
            self.equity_curve.append(equity_snapshot)

        return self._generate_results()

    def process_bar(self, df: pd.DataFrame, idx: int) -> float:
        """Process single price bar"""
        current_bar = df.iloc[idx]

        # Update position if exists
        if self.current_position is not None:
            self._check_position_exit(df, idx)

        # Check for new entry if no position
        elif idx >= 20:  # Need enough bars for indicators
            self._check_new_entry(df, idx)

        return self.equity

    def _check_position_exit(self, df: pd.DataFrame, idx: int):
        """Check and process position exits"""
        current_bar = df.iloc[idx]
        position = self.current_position

        # Update trailing stop
        new_trailing_stop = self.exit_rules.calculate_trailing_stop(
            df, idx, position.type, position.entry_price
        )
        position.trailing_stop = new_trailing_stop

        # Check stop loss and take profit
        hit_stop = (
            position.type == 'long' and current_bar['Low'] <= position.trailing_stop or
            position.type == 'short' and current_bar['High'] >= position.trailing_stop
        )

        hit_target = (
            position.type == 'long' and current_bar['High'] >= position.take_profit or
            position.type == 'short' and current_bar['Low'] <= position.take_profit
        )

        # Check exit signals
        should_exit, exit_details = self.exit_rules.check_exit_signals(
            df, idx, position.type
        )

        if hit_stop or hit_target or should_exit:
            exit_price = (
                position.trailing_stop if hit_stop else
                position.take_profit if hit_target else
                current_bar['Close']
            )

            self._close_position(exit_price, df.index[idx], 'Stop' if hit_stop else
                                 'Target' if hit_target else 'Signal')

    def _check_new_entry(self, df: pd.DataFrame, idx: int):
        """Check and process new position entries"""
        bullish, bearish, signal_details = self.entry_rules.check_entry_signals(
            df, idx)

        if bullish or bearish:
            position_type = 'long' if bullish else 'short'
            entry_price = df['Close'].iloc[idx]

            # Calculate position size and stops
            size = self.entry_rules.calculate_position_size(
                df, idx, self.position_size
            )

            stop_distance, take_profit_distance = (
                self.exit_rules.volatility_indicators.get_dynamic_stops(
                    df, idx)
            )

            stop_loss = (
                entry_price - stop_distance if position_type == 'long'
                else entry_price + stop_distance
            )

            take_profit = (
                entry_price + take_profit_distance if position_type == 'long'
                else entry_price - take_profit_distance
            )

            self._open_position(
                position_type,
                entry_price,
                df.index[idx],
                size,
                stop_loss,
                take_profit
            )

    def _open_position(self, type: str, price: float, time: pd.Timestamp,
                       size: float, stop_loss: float, take_profit: float):
        """Open new position"""
        self.trade_count += 1
        self.current_position = Position(
            type=type,
            entry_price=price,
            entry_time=time,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=stop_loss,
            trade_id=self.trade_count
        )

    def _close_position(self, exit_price: float, exit_time: pd.Timestamp,
                        exit_reason: str):
        """Close current position and record trade"""
        position = self.current_position

        # Calculate P&L
        if position.type == 'long':
            pnl = (exit_price - position.entry_price) * position.size
        else:
            pnl = (position.entry_price - exit_price) * position.size

        # Update equity
        self.equity += pnl

        # Record trade
        trade = {
            'id': position.trade_id,
            'type': position.type,
            'entry_time': position.entry_time,
            'entry_price': position.entry_price,
            'exit_time': exit_time,
            'exit_price': exit_price,
            'size': position.size,
            'pnl': pnl,
            'exit_reason': exit_reason
        }
        self.trades.append(trade)

        # Clear position
        self.current_position = None

    def _generate_results(self) -> Dict:
        """Generate backtest results summary"""
        equity_curve = pd.Series(self.equity_curve)

        results = {
            'initial_capital': self.initial_capital,
            'final_equity': self.equity,
            'total_return': (self.equity - self.initial_capital) / self.initial_capital,
            'trades': self.trades,
            'equity_curve': equity_curve,
            'trade_count': len(self.trades),
            'win_rate': sum(1 for t in self.trades if t['pnl'] > 0) / len(self.trades),
            'average_trade': np.mean([t['pnl'] for t in self.trades]),
            'max_drawdown': self._calculate_max_drawdown(equity_curve)
        }

        return results

    @staticmethod
    def _calculate_max_drawdown(equity_curve: pd.Series) -> float:
        """Calculate maximum drawdown"""
        rolling_max = equity_curve.expanding().max()
        drawdowns = equity_curve - rolling_max
        return abs(drawdowns.min())
