import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
import argparse

from config.strategy_config import StrategyConfig, DEFAULT_CONFIG
from src.patterns.candlestick_patterns import CandlestickPatterns
from src.patterns.momentum_patterns import MomentumPatterns
from src.indicators.momentum_indicators import MomentumIndicators, IndicatorParams
from src.indicators.volatility_indicators import VolatilityIndicators, VolatilityParams
from src.strategy.entry_rules import EntryRules
from src.strategy.exit_rules import ExitRules
from src.utils.data_loader import DataLoader
from src.utils.visualization import StrategyVisualizer
from src.backtester.backtest_engine import BacktestEngine
from src.backtester.performance_metrics import PerformanceMetrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_strategy(config: StrategyConfig):
    """Initialize strategy components"""
    # Initialize patterns
    candlestick_patterns = CandlestickPatterns()
    momentum_patterns = MomentumPatterns()

    # Initialize indicators
    indicator_params = IndicatorParams(
        rsi_period=config.indicators.rsi_period,
        macd_fast=config.indicators.macd_fast,
        macd_slow=config.indicators.macd_slow,
        macd_signal=config.indicators.macd_signal,
        bb_period=config.indicators.bb_period,
        bb_std=config.indicators.bb_std
    )

    volatility_params = VolatilityParams(
        atr_period=config.indicators.atr_period
    )

    momentum_indicators = MomentumIndicators(indicator_params)
    volatility_indicators = VolatilityIndicators(volatility_params)

    # Initialize rules
    entry_rules = EntryRules(
        candlestick_patterns,
        momentum_patterns,
        momentum_indicators,
        volatility_indicators
    )

    exit_rules = ExitRules(
        candlestick_patterns,
        momentum_patterns,
        momentum_indicators,
        volatility_indicators
    )

    return entry_rules, exit_rules


def run_backtest(config: StrategyConfig = DEFAULT_CONFIG):
    """Run strategy backtest"""
    logger.info("Starting strategy backtest...")

    try:
        # Load data
        data_loader = DataLoader()
        dfs = {}

        for symbol in config.backtest.symbols:
            logger.info(f"Loading data for {symbol}...")
            df = data_loader.load_from_yahoo(
                symbol,
                start_date=datetime.strptime(
                    config.backtest.start_date, '%Y-%m-%d') if config.backtest.start_date else None,
                end_date=datetime.strptime(
                    config.backtest.end_date, '%Y-%m-%d') if config.backtest.end_date else None
            )
            dfs[symbol] = data_loader.preprocess_data(df)

        # Initialize strategy components
        entry_rules, exit_rules = setup_strategy(config)

        # Run backtest for each symbol
        all_results = {}
        for symbol, df in dfs.items():
            logger.info(f"Running backtest for {symbol}...")

            backtest_engine = BacktestEngine(
                entry_rules,
                exit_rules,
                initial_capital=config.risk.initial_capital,
                position_size=config.risk.position_size
            )

            results = backtest_engine.run(df)
            all_results[symbol] = results

            # Calculate performance metrics
            metrics = PerformanceMetrics.calculate_metrics(
                results['trades'],
                results['equity_curve']
            )

            # Generate and save visualizations
            visualizer = StrategyVisualizer()

            # Create trading chart
            chart = visualizer.create_trading_chart(
                df,
                results['trades'],
                indicators=['RSI', 'MACD', 'BB_Upper', 'BB_Lower']
            )

            # Create performance dashboard
            dashboard = visualizer.create_performance_dashboard(metrics)

            # Save visualizations
            output_dir = Path('output') / \
                datetime.now().strftime('%Y%m%d_%H%M%S') / symbol
            output_dir.mkdir(parents=True, exist_ok=True)

            chart.write_html(output_dir / 'trading_chart.html')
            dashboard.write_html(output_dir / 'performance_dashboard.html')

            # Generate and save report
            report = PerformanceMetrics.generate_report(metrics)
            with open(output_dir / 'performance_report.txt', 'w') as f:
                f.write(report)

            logger.info(f"Results saved to {output_dir}")

        return all_results

    except Exception as e:
        logger.error(f"Error during backtest: {str(e)}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description='Run momentum trading strategy backtest')
    parser.add_argument('--config', type=str,
                        help='Path to configuration file')
    parser.add_argument('--symbols', nargs='+', help='Symbols to trade')
    parser.add_argument('--start-date', type=str,
                        help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    # Load configuration
    config = DEFAULT_CONFIG
    if args.config:
        # Load custom config from file
        pass

    # Override config with command line arguments
    if args.symbols:
        config.backtest.symbols = args.symbols
    if args.start_date:
        config.backtest.start_date = args.start_date
    if args.end_date:
        config.backtest.end_date = args.end_date

    # Validate configuration
    config.validate()

    # Run backtest
    results = run_backtest(config)

    logger.info("Backtest completed successfully")


if __name__ == "__main__":
    main()
