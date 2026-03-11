#!/usr/bin/env python3
"""Test script for backtester"""

from src.backtester import Backtester
import json

# Create mock prices (since we don't have real Alpaca API access)
prices = [
    {'timestamp': '2026-03-06T10:00:00', 'open': 178.5, 'high': 179.2, 'low': 178.1, 'close': 179.0, 'volume': 1000},
    {'timestamp': '2026-03-06T11:00:00', 'open': 179.0, 'high': 179.5, 'low': 178.8, 'close': 179.3, 'volume': 800},
    {'timestamp': '2026-03-06T12:00:00', 'open': 179.3, 'high': 180.1, 'low': 178.9, 'close': 180.0, 'volume': 1200},
    {'timestamp': '2026-03-07T10:00:00', 'open': 180.0, 'high': 181.5, 'low': 179.5, 'close': 181.0, 'volume': 1500},
    {'timestamp': '2026-03-07T11:00:00', 'open': 181.0, 'high': 182.0, 'low': 180.5, 'close': 181.8, 'volume': 900},
]

# Create signals
signals = [
    {'timestamp': '2026-03-06T09:00:00', 'signal': 'BUY', 'sentiment_score': 0.5, 'reason': 'Positive sentiment'},
    {'timestamp': '2026-03-07T10:00:00', 'signal': 'SELL', 'sentiment_score': -0.3, 'reason': 'Negative sentiment'},
]

print(f'Loaded {len(prices)} price records')
print(f'Loaded {len(signals)} signals')

# Run backtest
backtester = Backtester(initial_capital=10000)
results = backtester.simulate_trading(prices, signals)

print(f'\nBacktest Results:')
print(f'Final Portfolio Value: ${results.get("final_portfolio_value", 0):,.2f}')
print(f'Total Return: {results.get("total_return", 0):.2f}%')
print(f'Sharpe Ratio: {results.get("sharpe_ratio", 0):.4f}')
print(f'Max Drawdown: {results.get("max_drawdown", 0):.2f}%')

# Export report
backtester.export_report(results, 'results/backtest_report.txt')
