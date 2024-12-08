import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime


class PerformanceMetrics:
    @staticmethod
    def calculate_metrics(trades: List[Dict], equity_curve: pd.Series) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return {}

        # Convert trades to DataFrame
        trades_df = pd.DataFrame(trades)
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
        trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'])

        # Basic metrics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['pnl'] > 0)
        losing_trades = total_trades - winning_trades

        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # P&L metrics
        total_pnl = sum(t['pnl'] for t in trades)
        average_win = np.mean(
            [t['pnl'] for t in trades if t['pnl'] > 0]) if winning_trades > 0 else 0
        average_loss = np.mean(
            [t['pnl'] for t in trades if t['pnl'] <= 0]) if losing_trades > 0 else 0

        profit_factor = (
            sum(t['pnl'] for t in trades if t['pnl'] > 0) /
            abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0))
        ) if losing_trades > 0 else float('inf')

        # Risk metrics
        returns = equity_curve.pct_change().dropna()

        sharpe_ratio = np.sqrt(252) * (returns.mean() /
                                       returns.std()) if len(returns) > 0 else 0

        rolling_max = equity_curve.expanding().max()
        drawdowns = (equity_curve - rolling_max) / rolling_max
        max_drawdown = abs(drawdowns.min())

        # Time-based metrics
        duration = trades_df['exit_time'] - trades_df['entry_time']
        avg_trade_duration = duration.mean()

        # Monthly returns
        monthly_returns = returns.resample('M').apply(
            lambda x: (1 + x).prod() - 1
        )

        # Calculate MAR ratio (annualized return / max drawdown)
        total_days = (trades_df['exit_time'].max() -
                      trades_df['entry_time'].min()).days
        annualized_return = (
            (1 + total_pnl/equity_curve.iloc[0]) ** (365/total_days)) - 1
        mar_ratio = annualized_return / \
            max_drawdown if max_drawdown > 0 else float('inf')

        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'average_win': average_win,
            'average_loss': average_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'mar_ratio': mar_ratio,
            'average_trade_duration': avg_trade_duration,
            'monthly_returns': monthly_returns,
            'equity_curve': equity_curve,
            'drawdown': drawdowns,
            'annualized_return': annualized_return,

            # Additional trade analysis
            'long_trades': len(trades_df[trades_df['type'] == 'long']),
            'short_trades': len(trades_df[trades_df['type'] == 'short']),
            'avg_trade_pnl': total_pnl / total_trades if total_trades > 0 else 0,
            'best_trade': max(t['pnl'] for t in trades) if trades else 0,
            'worst_trade': min(t['pnl'] for t in trades) if trades else 0,
            'exit_reasons': trades_df['exit_reason'].value_counts().to_dict(),

            # Trade timing analysis
            'avg_bars_held': duration.mean().total_seconds() / (60 * 60 * 24),  # Convert to days
            'max_bars_held': duration.max().total_seconds() / (60 * 60 * 24),
            'min_bars_held': duration.min().total_seconds() / (60 * 60 * 24)
        }

    @staticmethod
    def generate_report(metrics: Dict) -> str:
        """Generate a formatted performance report"""
        report = [
            "=== Strategy Performance Report ===\n",
            f"Period: {metrics.get('start_date', 'N/A')} to {metrics.get('end_date', 'N/A')}\n",

            "\nTrade Statistics:",
            f"Total Trades: {metrics['total_trades']}",
            f"Win Rate: {metrics['win_rate']:.2%}",
            f"Profit Factor: {metrics['profit_factor']:.2f}",

            "\nReturns:",
            f"Total P&L: ${metrics['total_pnl']:,.2f}",
            f"Average Win: ${metrics['average_win']:,.2f}",
            f"Average Loss: ${metrics['average_loss']:,.2f}",
            f"Annualized Return: {metrics['annualized_return']:.2%}",

            "\nRisk Metrics:",
            f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}",
            f"Maximum Drawdown: {metrics['max_drawdown']:.2%}",
            f"MAR Ratio: {metrics['mar_ratio']:.2f}",

            "\nTrade Analysis:",
            f"Long Trades: {metrics['long_trades']}",
            f"Short Trades: {metrics['short_trades']}",
            f"Average Trade Duration: {metrics['avg_bars_held']:.1f} days",

            "\nExit Analysis:",
            "Exit Reasons Distribution:"
        ]

        for reason, count in metrics['exit_reasons'].items():
            report.append(f"- {reason}: {count} trades")

        return "\n".join(report)
