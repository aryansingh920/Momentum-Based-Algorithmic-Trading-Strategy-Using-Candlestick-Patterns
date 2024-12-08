import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional


class StrategyVisualizer:
    @staticmethod
    def create_trading_chart(df: pd.DataFrame,
                             trades: List[Dict],
                             indicators: Optional[List[str]] = None) -> go.Figure:
        """Create interactive trading chart with trades and indicators"""
        # Create figure with secondary y-axis
        fig = make_subplots(rows=2, cols=1,
                            shared_xaxes=True,
                            vertical_spacing=0.03,
                            row_heights=[0.7, 0.3])

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price'
            ),
            row=1, col=1
        )

        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume'
            ),
            row=2, col=1
        )

        # Add indicators if specified
        if indicators:
            for indicator in indicators:
                if indicator in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df[indicator],
                            name=indicator,
                            line=dict(width=1)
                        ),
                        row=1, col=1
                    )

        # Add trades
        for trade in trades:
            # Entry point
            fig.add_trace(
                go.Scatter(
                    x=[trade['entry_time']],
                    y=[trade['entry_price']],
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up' if trade['type'] == 'long' else 'triangle-down',
                        size=12,
                        color='green' if trade['type'] == 'long' else 'red'
                    ),
                    name=f"{trade['type'].capitalize()} Entry"
                ),
                row=1, col=1
            )

            # Exit point
            fig.add_trace(
                go.Scatter(
                    x=[trade['exit_time']],
                    y=[trade['exit_price']],
                    mode='markers',
                    marker=dict(
                        symbol='x',
                        size=12,
                        color='red' if trade['type'] == 'long' else 'green'
                    ),
                    name=f"{trade['type'].capitalize()} Exit"
                ),
                row=1, col=1
            )

        # Update layout
        fig.update_layout(
            title='Trading Strategy Performance',
            yaxis_title='Price',
            yaxis2_title='Volume',
            xaxis_rangeslider_visible=False
        )

        return fig

    @staticmethod
    def create_performance_dashboard(performance_metrics: Dict) -> go.Figure:
        """Create performance metrics dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Equity Curve',
                'Monthly Returns',
                'Drawdown',
                'Win/Loss Distribution'
            )
        )

        # Equity curve
        fig.add_trace(
            go.Scatter(
                x=performance_metrics['equity_curve'].index,
                y=performance_metrics['equity_curve'],
                name='Equity'
            ),
            row=1, col=1
        )

        # Monthly returns heatmap
        monthly_returns = performance_metrics['monthly_returns']
        fig.add_trace(
            go.Heatmap(
                z=monthly_returns.values.reshape(-1),
                x=monthly_returns.index,
                colorscale='RdYlGn',
                name='Monthly Returns'
            ),
            row=1, col=2
        )

        # Drawdown
        fig.add_trace(
            go.Scatter(
                x=performance_metrics['drawdown'].index,
                y=performance_metrics['drawdown'],
                fill='tozeroy',
                name='Drawdown'
            ),
            row=2, col=1
        )

        # Win/Loss distribution
        fig.add_trace(
            go.Bar(
                x=['Wins', 'Losses'],
                y=[
                    performance_metrics['win_rate'],
                    1 - performance_metrics['win_rate']
                ],
                name='Win/Loss'
            ),
            row=2, col=2
        )

        fig.update_layout(
            title='Strategy Performance Dashboard',
            showlegend=False,
            height=800
        )

        return fig
