"""
Visualization Dashboard (CLI)

CLI 可视化仪表板，展示 sentiment 趋势和交易信号。
"""

import argparse
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

from .alpaca_connector import AlpacaConnector
from .data_pipeline import DataPipeline
from .signal_generator import TradingSignal


class Dashboard:
    """CLI 可视化仪表板"""

    def __init__(self):
        """初始化仪表板"""
        self.alpaca = AlpacaConnector()

    def plot_sentiment_and_price(
        self,
        sentiment_data: dict,
        stock_prices: list,
        signals: list
    ):
        """
        创建双轴图表：sentiment 和 price

        Args:
            sentiment_data: 包含 timestamps 和 sentiments 的字典
            stock_prices: 价格数据列表
            signals: 交易信号列表
        """
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(12, 10),
            gridspec_kw={'height_ratios': [2, 1]}
        )

        # 第一个图：Sentiment 和股价
        self._plot_sentiment(ax1, sentiment_data)
        self._plot_prices(ax1, stock_prices)

        # 标记买入/卖出信号
        self._plot_signals(ax1, signals, stock_prices)

        ax1.set_title('Commit Sentiment & Stock Price', fontsize=14, fontweight='bold')
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)

        # 第二个图：Sentiment 时间序列
        self._plot_sentiment_only(ax2, sentiment_data)

        plt.tight_layout()
        plt.show()

    def _plot_sentiment(self, ax, sentiment_data: dict):
        """绘制 sentiment 曲线"""
        timestamps = sentiment_data.get("timestamps", [])
        sentiments = sentiment_data.get("sentiments", [])

        if not timestamps or not sentiments:
            return

        # 转换时间戳
        dates = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in timestamps]

        ax.plot(dates, sentiments, 'b-', label='Sentiment Score', alpha=0.8)
        ax.axhline(y=0.3, color='g', linestyle='--', label='Buy Threshold', alpha=0.5)
        ax.axhline(y=-0.3, color='r', linestyle='--', label='Sell Threshold', alpha=0.5)
        ax.fill_between(
            [d for d in dates], -0.3, 0.3,
            facecolor='gray', alpha=0.1, label='Neutral Zone'
        )

    def _plot_prices(self, ax, stock_prices: list):
        """绘制股价曲线（右轴）"""
        if not stock_prices:
            return

        prices = []
        dates = []

        for price in stock_prices:
            if "timestamp" in price and "close" in price:
                try:
                    dates.append(price["timestamp"])
                    prices.append(price["close"])
                except (ValueError, TypeError):
                    continue

        if not prices:
            return

        # 使用双轴显示股价
        ax2 = ax.twinx()
        ax2.plot(dates, prices, 'orange', label='Stock Price', alpha=0.7)
        ax2.set_ylabel('Price (USD)', color='orange')
        ax2.tick_params(axis='y', colors='orange')

    def _plot_signals(self, ax, signals: list, stock_prices: list):
        """标记买入/卖出信号（三角形图标）"""
        if not signals or not stock_prices:
            return

        prices = {i: p for i, p in enumerate(stock_prices)}
        price_map = {}
        for i, p in enumerate(stock_prices):
            if "timestamp" in p and "close" in p:
                try:
                    price_map[i] = {"timestamp": p["timestamp"], "close": p["close"]}
                except (ValueError, TypeError):
                    continue

        # 获取价格范围用于定位信号
        min_price = min(p.get("close", 0) for p in stock_prices if "close" in p)
        max_price = max(p.get("close", 0) for p in stock_prices if "close" in p)

        signal_y_offset = (max_price - min_price) * 0.05

        for signal in signals:
            if signal.get("signal") == TradingSignal.BUY.value:
                # 找到最近的价格点
                ax.scatter(
                    len(prices) // 2, min_price - signal_y_offset,
                    marker='^', color='green', s=100,
                    label='BUY Signal' if 'BUY' not in str(ax.get_legend().get_texts()) else ''
                )
            elif signal.get("signal") == TradingSignal.SELL.value:
                ax.scatter(
                    len(prices) // 2, max_price + signal_y_offset,
                    marker='v', color='red', s=100,
                    label='SELL Signal' if 'SELL' not in str(ax.get_legend().get_texts()) else ''
                )

    def _plot_sentiment_only(self, ax, sentiment_data: dict):
        """仅绘制 sentiment 时间序列"""
        timestamps = sentiment_data.get("timestamps", [])
        sentiments = sentiment_data.get("sentiments", [])

        if not timestamps or not sentiments:
            return

        dates = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in timestamps]

        ax.plot(dates, sentiments, 'b-', label='Sentiment')
        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        ax.fill_between(
            [d for d in dates], 0, sentiments,
            where=[s > 0 for s in sentiments],
            facecolor='green', alpha=0.2, label='Positive'
        )
        ax.fill_between(
            [d for d in dates], 0, sentiments,
            where=[s < 0 for s in sentiments],
            facecolor='red', alpha=0.2, label='Negative'
        )

        ax.set_ylabel('Sentiment Score')
        ax.grid(True, alpha=0.3)

    def display_summary(self, sentiment_data: dict, signals: list):
        """
        显示摘要信息

        Args:
            sentiment_data: 情感数据
            signals: 交易信号
        """
        print("\n" + "=" * 50)
        print("COMMIT SENTIMENT TRADER - SUMMARY")
        print("=" * 50)

        sentiments = sentiment_data.get("sentiments", [])
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            print(f"\nAverage Sentiment: {avg_sentiment:.3f}")

            positive = sum(1 for s in sentiments if s > 0.3)
            negative = sum(1 for s in sentiments if s < -0.3)
            neutral = len(sentiments) - positive - negative

            print(f"Positive Commits:   {positive} ({positive/len(sentiments)*100:.1f}%)")
            print(f"Neutral Commits:    {neutral} ({neutral/len(sentiments)*100:.1f}%)")
            print(f"Negative Commits:   {negative} ({negative/len(sentiments)*100:.1f}%)")

        # 信号摘要
        if signals:
            buy_count = sum(1 for s in signals if s.get("signal") == TradingSignal.BUY.value)
            sell_count = sum(1 for s in signals if s.get("signal") == TradingSignal.SELL.value)

            print(f"\nTotal Signals: {len(signals)}")
            print(f"Buy Signals:   {buy_count}")
            print(f"Sell Signals:  {sell_count}")

        # 最新信号
        if signals:
            latest = signals[-1]
            print(f"\nLatest Signal: {latest.get('signal', 'N/A')}")
            print(f"At: {latest.get('timestamp', 'N/A')}")
            print(f"Sentiment Score: {latest.get('sentiment_score', 'N/A'):.3f}")

        print("\n" + "=" * 50)


# 命令行接口
def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Commit Sentiment Trader - CLI Dashboard'
    )
    parser.add_argument('--repo', type=str, default='tensorflow/tensorflow',
                        help='GitHub repository (owner/repo)')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to analyze')
    parser.add_argument('--symbol', type=str, default='AAPL',
                        help='Stock symbol to analyze')

    args = parser.parse_args()

    # 初始化仪表板
    dashboard = Dashboard()

    # 解析仓库信息
    repo_parts = args.repo.split('/')
    if len(repo_parts) != 2:
        print("Error: Repository must be in format owner/repo")
        return

    owner, repo = repo_parts

    try:
        # 获取和分析数据
        pipeline = DataPipeline()
        result = pipeline.fetch_and_process_repo(owner, repo)

        if "error" in result:
            print(f"Error processing repository: {result['error']}")
            return

        # 获取股价数据
        prices = dashboard.alpaca.get_stock_prices(args.symbol)

        # 绘制图表
        dashboard.plot_sentiment_and_price(
            result["time_series"],
            prices,
            result["signals"]
        )

        # 显示摘要
        dashboard.display_summary(result["time_series"], result["signals"])

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
