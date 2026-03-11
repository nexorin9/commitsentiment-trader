#!/usr/bin/env python3
"""
Test script for multiple repository analysis.

This script loads pre-cached commit data from 3 different repositories
(Python, JavaScript, Go) to demonstrate the sentiment analysis pipeline
without requiring live API access.
"""

import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from github_fetcher import GitHubFetcher
from sentiment_analyzer import CommitSentimentAnalyzer
from time_series import SentimentTimeSeries
from signal_generator import SignalGenerator
from alpaca_connector import AlpacaConnector
from backtester import Backtester

# Three repositories to test (simulated with cached data)
REPOSITORIES = [
    {
        "owner": "tensorflow",
        "repo": "tensorflow",
        "name": "TensorFlow",
        "language": "Python",
        "category": "ML/AI Framework",
        "commits_file": "data/tensorflow_tensorflow_commits.json"
    },
    {
        "owner": "nodejs",
        "repo": "node",
        "name": "Node.js",
        "language": "JavaScript",
        "category": "Runtime Environment",
        "commits_file": "data/nodejs_node_commits.json"
    },
    {
        "owner": "golang",
        "repo": "go",
        "name": "Go",
        "language": "Go",
        "category": "Programming Language",
        "commits_file": "data/golang_go_commits.json"
    }
]


def load_commits_from_file(commits_file):
    """Load commits from a JSON file instead of API."""
    if not os.path.exists(commits_file):
        print(f"  Warning: {commits_file} not found")
        return []

    with open(commits_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('commits', [])


def analyze_repository(repo_info):
    """Analyze a single repository's commits for sentiment."""
    owner = repo_info['owner']
    repo = repo_info['repo']
    name = repo_info['name']
    language = repo_info['language']

    print(f"\n{'='*60}")
    print(f"Analyzing {name} ({language})")
    print(f"Repository: {owner}/{repo}")
    print('='*60)

    # Load cached commits
    commits = load_commits_from_file(repo_info['commits_file'])

    if not commits:
        return None

    print(f"Loaded {len(commits)} commits from cache")

    # Initialize analyzer
    analyzer = CommitSentimentAnalyzer()

    # Extract messages
    messages = []
    for commit in commits:
        if "commit" in commit and "message" in commit["commit"]:
            messages.append(commit["commit"]["message"])

    # Analyze sentiments
    sentiments = analyzer.analyze_commits(messages)

    # Calculate metrics
    avg_sentiment = sum(s["compound"] for s in sentiments) / len(sentiments) if sentiments else 0
    positive_count = sum(1 for s in sentiments if s["compound"] > 0.3)
    negative_count = sum(1 for s in sentiments if s["compound"] < -0.3)
    neutral_count = len(sentiments) - positive_count - negative_count
    positive_ratio = positive_count / len(sentiments) if sentiments else 0

    print(f"\nSentiment Analysis Results:")
    print(f"  Total commits analyzed: {len(messages)}")
    print(f"  Average sentiment score: {avg_sentiment:.4f}")
    print(f"  Positive ratio: {positive_ratio:.2%}")
    print(f"  Positive commits: {positive_count}")
    print(f"  Negative commits: {negative_count}")
    print(f"  Neutral commits: {neutral_count}")

    # Get sample sentiments
    print(f"\nSample commit sentiments:")
    for i, (msg, sent) in enumerate(zip(messages[:3], sentiments[:3])):
        print(f"  {i+1}. [{msg[:60]}...]")
        print(f"     Sentiment: {sent['compound']:.3f} (pos={sent['pos']:.2f}, neg={sent['neg']:.2f})")

    # Build time series
    ts_engine = SentimentTimeSeries()
    time_series_df = ts_engine.calculate_rolling_sentiment(commits)

    data_dict = {
        "timestamps": [str(ts) for ts in time_series_df.index],
        "sentiments": time_series_df["sentiment"].tolist()
    }

    # Generate signals
    signal_gen = SignalGenerator(threshold=0.3)
    signals = signal_gen.generate_signals(data_dict)

    buy_signals = sum(1 for s in signals if s["signal"] == "BUY")
    sell_signals = sum(1 for s in signals if s["signal"] == "SELL")

    print(f"\nTrading Signals:")
    print(f"  Total signals: {len(signals)}")
    print(f"  BUY signals: {buy_signals}")
    print(f"  SELL signals: {sell_signals}")

    # Mock backtest (using synthetic price data since we don't have Alpaca token)
    print(f"\nBacktest (Synthetic Prices - No API Token):")
    print(f"  Note: Real backtest requires Alpaca API credentials")
    print(f"  Using mock data for demonstration...")

    mock_prices = [100 + (i * 0.5) + (s * 10) for i, s in enumerate(data_dict["sentiments"])]
    mock_signals = [{"timestamp": s["timestamp"], "signal": s["signal"], "price": mock_prices[i]} for i, s in enumerate(signals)]

    initial_capital = 10000
    shares = 0
    cash = initial_capital
    portfolio_values = []

    for i, signal in enumerate(mock_signals):
        price = mock_prices[i] if i < len(mock_prices) else mock_prices[-1]

        if signal["signal"] == "BUY" and cash >= price * 10:
            shares += 10
            cash -= price * 10
        elif signal["signal"] == "SELL" and shares >= 10:
            shares -= 10
            cash += price * 10

        portfolio_value = cash + (shares * price)
        portfolio_values.append(portfolio_value)

    final_value = portfolio_values[-1] if portfolio_values else initial_capital
    total_return = ((final_value - initial_capital) / initial_capital) * 100

    print(f"  Initial capital: ${initial_capital:.2f}")
    print(f"  Final value: ${final_value:.2f}")
    print(f"  Total return: {total_return:.2f}%")

    return {
        "name": name,
        "language": language,
        "repo": f"{owner}/{repo}",
        "commits_count": len(messages),
        "avg_sentiment": avg_sentiment,
        "positive_ratio": positive_ratio,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "total_signals": len(signals),
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "final_value": final_value,
        "total_return": total_return
    }


def generate_comparison_report(results):
    """Generate comparison report across all repositories."""
    print(f"\n{'='*60}")
    print("MULTI-REPOSITORY COMPARISON REPORT")
    print('='*60)

    # Table header
    print(f"\n{'Repository':<20} {'Lang':<10} {'Commits':>8} {'Avg Sent':>10} {'Pos Ratio':>10} {'Buy':>5} {'Sell':>5} {'Return':>10}")
    print("-" * 80)

    for r in results:
        print(f"{r['name']:<20} {r['language']:<10} {r['commits_count']:>8} {r['avg_sentiment']:>10.4f} {r['positive_ratio']:>10.2%} {r['buy_signals']:>5} {r['sell_signals']:>5} {r['total_return']:>9.2f}%")

    print("-" * 80)

    # Key observations
    best_sentiment = max(results, key=lambda x: x['avg_sentiment'])
    worst_sentiment = min(results, key=lambda x: x['avg_sentiment'])
    highest_positive = max(results, key=lambda x: x['positive_ratio'])

    print(f"\nKey Observations:")
    print(f"  Highest average sentiment: {best_sentiment['name']} ({best_sentiment['avg_sentiment']:.4f})")
    print(f"  Lowest average sentiment: {worst_sentiment['name']} ({worst_sentiment['avg_sentiment']:.4f})")
    print(f"  Highest positive ratio: {highest_positive['name']} ({highest_positive['positive_ratio']:.2%})")

    # Pattern analysis
    print(f"\nPattern Analysis:")

    # Check if positive sentiment correlates with positive return
    positive_return_count = sum(1 for r in results if r['total_return'] > 0)
    print(f"  Repositories with positive mock returns: {positive_return_count}/{len(results)}")

    # Note about language differences
    print(f"\nLanguage Pattern Notes:")
    python_repos = [r for r in results if 'Python' in r['language']]
    js_repos = [r for r in results if 'JavaScript' in r['language']]
    go_repos = [r for r in results if 'Go' in r['language']]

    if python_repos:
        avg_python = sum(r['avg_sentiment'] for r in python_repos) / len(python_repos)
        print(f"  Python projects avg sentiment: {avg_python:.4f}")
    if js_repos:
        avg_js = sum(r['avg_sentiment'] for r in js_repos) / len(js_repos)
        print(f"  JavaScript projects avg sentiment: {avg_js:.4f}")
    if go_repos:
        avg_go = sum(r['avg_sentiment'] for r in go_repos) / len(go_repos)
        print(f"  Go projects avg sentiment: {avg_go:.4f}")


def main():
    """Main entry point."""
    print("="*60)
    print("MULTI-REPOSITORY SENTIMENT ANALYSIS TEST")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Note: Using cached commit data (no live API calls)")
    print(f"Repositories: TensorFlow (Python), Node.js (JavaScript), Go (Go)")

    results = []

    for repo_info in REPOSITORIES:
        result = analyze_repository(repo_info)
        if result:
            results.append(result)

    if results:
        generate_comparison_report(results)

        # Save detailed results
        os.makedirs("results", exist_ok=True)
        with open("results/multi_repo_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to results/multi_repo_analysis.json")
    else:
        print("\nNo results to analyze. Check data files.")

    print(f"\nTest completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
