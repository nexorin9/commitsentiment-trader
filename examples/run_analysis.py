#!/usr/bin/env python3
"""
Example Script - Commit Sentiment Trader

展示如何使用项目进行分析。
"""

import argparse
import json
import os
import sys
from datetime import datetime

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from github_fetcher import GitHubFetcher
from sentiment_analyzer import CommitSentimentAnalyzer
from time_series import SentimentTimeSeries
from signal_generator import SignalGenerator
from alpaca_connector import AlpacaConnector
from backtester import Backtester


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Run commit sentiment analysis and trading signal generation'
    )
    parser.add_argument('--repo', type=str, default='tensorflow/tensorflow',
                        help='GitHub repository (owner/repo)')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to analyze')
    parser.add_argument('--symbol', type=str, default='AAPL',
                        help='Stock symbol to analyze')
    parser.add_argument('--threshold', type=float, default=0.3,
                        help='Sentiment threshold for signals')
    parser.add_argument('--output-dir', type=str, default='results',
                        help='Output directory for results')

    return parser.parse_args()


def main():
    """主函数 - 运行完整分析流程"""
    args = parse_args()

    print("=" * 60)
    print("COMMIT SENTIMENT TRADER")
    print(f"Repository: {args.repo}")
    print(f"Stock Symbol: {args.symbol}")
    print(f"Analysis Period: {args.days} days")
    print("=" * 60)

    # 解析仓库信息
    repo_parts = args.repo.split('/')
    if len(repo_parts) != 2:
        print("Error: Repository must be in format owner/repo")
        sys.exit(1)

    owner, repo = repo_parts

    try:
        # Step 1: 获取 commits
        print("\n[1/5] Fetching commits...")
        fetcher = GitHubFetcher()
        commits = fetcher.fetch_commits(owner, repo)
        print(f"  Fetched {len(commits)} commits")

        # Step 2: 分析情感
        print("\n[2/5] Analyzing sentiment...")
        analyzer = CommitSentimentAnalyzer()
        messages = []
        for commit in commits:
            if "commit" in commit and "message" in commit["commit"]:
                messages.append(commit["commit"]["message"])

        sentiments = analyzer.analyze_commits(messages)
        avg_sentiment = sum(s["compound"] for s in sentiments) / len(sentiments) if sentiments else 0
        print(f"  Analyzed {len(messages)} commits")
        print(f"  Average sentiment: {avg_sentiment:.3f}")

        # Step 3: 构建时间序列
        print("\n[3/5] Building time series...")
        ts_engine = SentimentTimeSeries()
        time_series_df = ts_engine.calculate_rolling_sentiment(commits)

        data_dict = {
            "timestamps": [str(ts) for ts in time_series_df.index],
            "sentiments": time_series_df["sentiment"].tolist()
        }
        print(f"  Generated {len(data_dict['sentiments'])} time points")

        # Step 4: 生成信号
        print("\n[4/5] Generating signals...")
        signal_gen = SignalGenerator(threshold=args.threshold)
        signals = signal_gen.generate_signals(data_dict)

        buy_count = sum(1 for s in signals if s["signal"] == "BUY")
        sell_count = sum(1 for s in signals if s["signal"] == "SELL")
        print(f"  Generated {len(signals)} total signals")
        print(f"  BUY: {buy_count}, SELL: {sell_count}")

        # Step 5: 获取股价数据并回测
        print("\n[5/5] Running backtest...")
        alpaca = AlpacaConnector()
        prices = alpaca.get_stock_prices(args.symbol, limit=100)

        if prices:
            backtester = Backtester()
            results = backtester.simulate_trading(prices, signals)
            backtester.export_report(results, os.path.join(args.output_dir, "backtest_report.txt"))

            print(f"  Final Portfolio Value: ${results.get('final_portfolio_value', 0):,.2f}")
            print(f"  Total Return: {results.get('total_return', 0):.2f}%")
            print(f"  Sharpe Ratio: {results.get('sharpe_ratio', 0):.4f}")

        # 保存结果
        os.makedirs(args.output_dir, exist_ok=True)

        # 保存原始数据
        with open(os.path.join(args.output_dir, "commits.json"), "w") as f:
            json.dump({
                "owner": owner,
                "repo": repo,
                "timestamp": datetime.now().isoformat(),
                "commits_count": len(commits),
                "sample_commits": commits[:10]  # 保存前10个作为示例
            }, f, indent=2)

        with open(os.path.join(args.output_dir, "sentiment_data.json"), "w") as f:
            json.dump(data_dict, f, indent=2)

        with open(os.path.join(args.output_dir, "signals.json"), "w") as f:
            signal_gen.save_signals(signals, os.path.join(args.output_dir, "signals.json"))

        print("\n" + "=" * 60)
        print("Analysis complete. Results saved to:", args.output_dir)
        print("=" * 60)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
