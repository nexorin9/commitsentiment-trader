"""
Backtesting Engine

使用历史数据验证交易策略的有效性。
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


class Backtester:
    """回测引擎"""

    def __init__(
        self,
        initial_capital: float = 10000,
        commission: float = 0.0  # 每笔交易的佣金（百分比）
    ):
        """
        初始化回测器

        Args:
            initial_capital: 初始资金
            commission: 每笔交易的佣金比例
        """
        self.initial_capital = initial_capital
        self.commission = commission

    def simulate_trading(
        self,
        prices: List[Dict],
        signals: List[Dict]
    ) -> Dict:
        """
        运行交易模拟

        Args:
            prices: 价格数据列表，包含 timestamp 和 price
            signals: 信号列表，包含 timestamp 和 signal

        Returns:
            包含回测结果的字典
        """
        if not prices or not signals:
            return {"error": "No data provided"}

        # 创建 DataFrame
        price_df = pd.DataFrame(prices)
        price_df["timestamp"] = pd.to_datetime(price_df["timestamp"]).dt.tz_localize(None)
        price_df.set_index("timestamp", inplace=True)

        # 创建信号 DataFrame
        signal_df = pd.DataFrame(signals)
        signal_df["timestamp"] = pd.to_datetime(signal_df["timestamp"]).dt.tz_localize(None)
        signal_df.set_index("timestamp", inplace=True)

        # 合并数据
        df = price_df.copy()
        df["signal"] = signal_df["signal"].reindex(df.index, method="ffill").fillna("HOLD")

        # 计算持仓
        df["position"] = 0
        for i, row in df.iterrows():
            if row["signal"] == "BUY":
                df.loc[i, "position"] = 1
            elif row["signal"] == "SELL":
                df.loc[i, "position"] = -1

        # 计算收益率
        df["returns"] = df["close"].pct_change()
        df["strategy_returns"] = df["position"].shift() * df["returns"]

        # 计算累计收益
        df["cumulative_market"] = (1 + df["returns"]).cumprod()
        df["cumulative_strategy"] = (1 + df["strategy_returns"]).cumprod()

        # 计算绩效指标
        results = self._calculate_metrics(df)

        return {
            "final_portfolio_value": results["final_portfolio_value"],
            "total_return": results["total_return"],
            "market_return": results["market_return"],
            "sharpe_ratio": results["sharpe_ratio"],
            "max_drawdown": results["max_drawdown"],
            "win_rate": results["win_rate"],
            "profit_factor": results["profit_factor"],
            "trades_count": results["trades_count"],
            "data": df
        }

    def _calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """
        计算回测绩效指标

        Args:
            df: 包含策略数据的 DataFrame

        Returns:
            包含各项指标的字典
        """
        # 最终投资组合价值
        capital = self.initial_capital
        cumulative = df["cumulative_strategy"].fillna(1)
        final_value = capital * cumulative.iloc[-1]

        # 总收益率
        total_return = (df["cumulative_strategy"].iloc[-1] - 1) * 100

        # 市场收益率（基准）
        market_return = (df["cumulative_market"].iloc[-1] - 1) * 100

        # 夏普比率
        strategy_rets = df["strategy_returns"].dropna()
        if len(strategy_rets) > 1 and strategy_rets.std() != 0:
            sharpe_ratio = (
                strategy_rets.mean() / strategy_rets.std()
            ) * np.sqrt(252)  # 年化（假设日交易）
        else:
            sharpe_ratio = 0

        # 最大回撤
        cumulative_values = (1 + strategy_rets.cumsum()).fillna(1)
        running_max = cumulative_values.cummax()
        drawdown = (running_max - cumulative_values) / running_max
        max_drawdown = drawdown.max() * 100 if len(drawdown) > 0 else 0

        # 胜率和盈亏比
        trades = []
        positions = df["position"].fillna(0)
        prev_pos = 0
        entry_price = 0

        for ts, row in df.iterrows():
            curr_pos = row["position"]
            if curr_pos != 0 and prev_pos == 0:
                # 入场
                entry_price = row["close"]
            elif curr_pos == 0 and prev_pos != 0:
                # 出场
                trades.append({
                    "return": (row["close"] - entry_price) / entry_price * 100,
                    "timestamp": ts
                })
            prev_pos = curr_pos

        win_count = sum(1 for t in trades if t["return"] > 0)
        win_rate = win_count / len(trades) if trades else 0

        # 盈亏比（平均盈利/平均亏损）
        profits = [t["return"] for t in trades if t["return"] > 0]
        losses = [-t["return"] for t in trades if t["return"] < 0]

        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = sum(losses) / len(losses) if losses else 1

        profit_factor = avg_profit / avg_loss if avg_loss != 0 else 1

        return {
            "final_portfolio_value": final_value,
            "total_return": total_return,
            "market_return": market_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate * 100,
            "profit_factor": profit_factor,
            "trades_count": len(trades)
        }

    def export_report(self, results: Dict, output_path: str):
        """
        导出回测报告

        Args:
            results: 回测结果字典
            output_path: 输出文件路径
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        report = f"""
=== Backtest Report ===

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

--- Performance Metrics ---

Initial Capital: ${self.initial_capital:,.2f}
Final Portfolio Value: ${results.get('final_portfolio_value', 0):,.2f}

Total Return: {results.get('total_return', 0):.2f}%
Market Return (Buy & Hold): {results.get('market_return', 0):.2f}%

Sharpe Ratio: {results.get('sharpe_ratio', 0):.4f}
Maximum Drawdown: {results.get('max_drawdown', 0):.2f}%

--- Trading Statistics ---

Win Rate: {results.get('win_rate', 0):.2f}%
Profit Factor: {results.get('profit_factor', 0):.4f}
Total Trades: {results.get('trades_count', 0)}

--- Strategy Summary ---

{'Outperformed Market' if results.get('total_return', 0) > results.get('market_return', 0) else 'Underperformed Market'} by {abs(results.get('total_return', 0) - results.get('market_return', 0)):.2f}%

---
Note: This is a simplified backtest. Real trading involves additional factors
like slippage, order execution timing, and market impact.
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"Backtest report saved to {output_path}")


# 方便使用的函数
def simulate_trading(prices: List[Dict], signals: List[Dict]) -> Dict:
    """
    快速回测的便捷函数

    Args:
        prices: 价格数据
        signals: 信号数据

    Returns:
        回测结果字典
    """
    backtester = Backtester()
    return backtester.simulate_trading(prices, signals)


def export_report(results: Dict, output_path: str):
    """导出报告的便捷函数"""
    backtester = Backtester()
    backtester.export_report(results, output_path)


def generate_report(
    results: Dict,
    repository: str,
    date_range: str,
    symbol: str,
    output_path: str,
    sentiment_data: Dict = None
):
    """
    使用模板生成完整的分析报告

    Args:
        results: 回测结果字典
        repository: GitHub 仓库名称 (owner/repo)
        date_range: 分析日期范围
        symbol: 股票代码
        output_path: 输出文件路径
        sentiment_data: 情感数据字典 (可选)

    Returns:
        生成的报告路径
    """
    import os
    from datetime import datetime

    # 读取模板
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'report_template.md')
    if not os.path.exists(template_path):
        # Fallback: create inline report
        report = export_report_inline(results, repository, output_path)
        return report

    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # 填充模板变量
    sentiment_stats = sentiment_data if sentiment_data else {}

    # 计算情感统计
    commits_count = sentiment_stats.get('commits_count', 0)
    avg_sentiment = sentiment_stats.get('avg_sentiment', 0)
    positive_ratio = sentiment_stats.get('positive_ratio', 0)
    negative_ratio = sentiment_stats.get('negative_ratio', 0)

    # 构建报告内容
    report = template.format(
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        repo=repository,
        date_range=date_range,
        num_time_points=sentiment_stats.get('num_time_points', 0),
        symbol=symbol,
        threshold=sentiment_stats.get('threshold', 0.3),
        commits_count=commits_count,
        avg_sentiment=avg_sentiment,
        positive_ratio=positive_ratio,
        neutral_ratio=sentiment_stats.get('neutral_ratio', 1 - positive_ratio - negative_ratio),
        negative_ratio=negative_ratio,
        positive_count=sentiment_stats.get('positive_count', 0),
        neutral_count=sentiment_stats.get('neutral_count', 0),
        negative_count=sentiment_stats.get('negative_count', 0),
        positive_sample_1=sentiment_stats.get('positive_sample_1', 'N/A'),
        positive_score_1=sentiment_stats.get('positive_score_1', 0),
        positive_sample_2=sentiment_stats.get('positive_sample_2', 'N/A'),
        positive_score_2=sentiment_stats.get('positive_score_2', 0),
        neutral_sample_1=sentiment_stats.get('neutral_sample_1', 'N/A'),
        neutral_score_1=sentiment_stats.get('neutral_score_1', 0),
        negative_sample_1=sentiment_stats.get('negative_sample_1', 'N/A'),
        negative_score_1=sentiment_stats.get('negative_score_1', 0),
        buy_signals=results.get('buy_signals', 0),
        sell_signals=results.get('sell_signals', 0),
        hold_signals=results.get('hold_signals', 0),
        total_signals=results.get('total_signals', 0),
        first_signal_date=sentiment_stats.get('first_signal_date', 'N/A'),
        last_signal_date=sentiment_stats.get('last_signal_date', 'N/A'),
        signal_density=sentiment_stats.get('signal_density', 0),
        initial_capital=10000,
        final_value=results.get('final_value', 0),
        total_return=results.get('total_return', 0),
        market_return=results.get('market_return', 0),
        alpha=results.get('total_return', 0) - results.get('market_return', 0),
        sharpe_ratio=results.get('sharpe_ratio', 0),
        max_drawdown=results.get('max_drawdown', 0),
        win_rate=results.get('win_rate', 0),
        profit_factor=results.get('profit_factor', 0),
        trades_count=results.get('trades_count', 0),
        window_hours=sentiment_stats.get('window_hours', 24),
        config_file=sentiment_stats.get('config_file', 'N/A'),
        signals_table=results.get('signals_table', 'N/A')
    )

    # 确保目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    return output_path


def export_report_inline(results: Dict, repository: str, output_path: str) -> str:
    """
    内联生成报告（当模板缺失时）
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    report = f"""# CommitSentiment Trader 分析报告

## 概览
- **仓库**: {repository}
- **报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **版本**: 1.0

## 关键指标
- **总收益**: {results.get('total_return', 0):.2f}%
- **夏普比率**: {results.get('sharpe_ratio', 0):.4f}
- **最大回撤**: {results.get('max_drawdown', 0):.2f}%
- **交易次数**: {results.get('trades_count', 0)}

## 情感分析
- **平均情感分数**: {results.get('avg_sentiment', 0):.4f}
- **正向比例**: {results.get('positive_ratio', 0):.2%}

## 信号统计
- **买入信号**: {results.get('buy_signals', 0)}
- **卖出信号**: {results.get('sell_signals', 0)}
- **持有信号**: {results.get('hold_signals', 0)}

---

*本报告由 CommitSentiment Trader 自动生成*
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    return output_path
