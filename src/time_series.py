"""
Sentiment Time Series Engine

将离散的 commits 转换为平滑的情感趋势数据。
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import numpy as np

# Import sentiment analyzer
from sentiment_analyzer import analyze_commit


class SentimentTimeSeries:
    """情感时间序列引擎"""

    def __init__(self):
        """初始化时间序列引擎"""
        self.default_window_hours = 24

    def calculate_rolling_sentiment(
        self,
        commits: List[Dict],
        window_hours: int = 24
    ) -> pd.DataFrame:
        """
        计算滚动情感时间序列

        Args:
            commits: Commit 列表，每个 commit 应包含 'commit' 和 'sender' 等信息
            window_hours: 滚动窗口大小（小时）

        Returns:
            包含时间序列数据的 DataFrame
        """
        if not commits:
            return pd.DataFrame()

        # 解析 commit 数据并提取关键信息
        data = []
        for commit in commits:
            commit_data = self._parse_commit(commit)
            if commit_data:
                # Add sentiment score to parsed data
                msg = commit.get("commit", {}).get("message", "")
                scores = analyze_commit(msg)
                commit_data["compound"] = scores.get("compound", 0.0)
                data.append(commit_data)

        if not data:
            return pd.DataFrame()

        # 创建 DataFrame
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # 按小时频率重采样并计算平均 sentiment
        df.set_index("timestamp", inplace=True)

        # 获取完整的时间范围
        start_time = df.index.min()
        end_time = df.index.max()

        # 创建完整的小时索引 (use 'h' instead of deprecated 'H')
        full_range = pd.date_range(
            start=start_time.replace(minute=0, second=0, microsecond=0),
            end=end_time,
            freq="h"
        )

        # 重采样计算每小时平均 sentiment
        hourly_df = df["compound"].resample("h").mean()

        # 填充缺失值（向前填充，使用 ffill 代替已废弃的 fillna method 参数）
        hourly_df = hourly_df.ffill().fillna(0)

        # 转换回 DataFrame
        result_df = pd.DataFrame({
            "timestamp": full_range,
            "sentiment": hourly_df.values
        })
        result_df.set_index("timestamp", inplace=True)

        return result_df

    def _parse_commit(self, commit: Dict) -> Optional[Dict]:
        """
        解析单个 commit 获取关键信息

        Args:
            commit: GitHub API 返回的 commit 数据

        Returns:
            包含 timestamp 和 compound score 的字典
        """
        try:
            # 尝试多种可能的数据结构
            if isinstance(commit, dict):
                # 提取时间戳
                if "commit" in commit and "committer" in commit["commit"]:
                    date_str = commit["commit"]["committer"].get("date")
                elif "commit" in commit and "author" in commit["commit"]:
                    date_str = commit["commit"]["author"].get("date")
                else:
                    return None

                if not date_str:
                    return None

                timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

                # 提取 sender 信息用于权重
                sender = commit.get("author", {}).get("login") or "unknown"

                return {
                    "timestamp": timestamp,
                    "sender": sender
                }
            return None
        except (KeyError, ValueError, TypeError):
            return None

    def add_trend_detection(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加趋势检测：使用简单线性回归检测情感变化方向

        Args:
            df: 包含 sentiment 列的 DataFrame

        Returns:
            添加 trend_direction 和 trend_strength 列的 DataFrame
        """
        if df.empty or len(df) < 2:
            df["trend_direction"] = 0
            df["trend_strength"] = 0
            return df

        # 计算线性回归斜率
        x = np.arange(len(df))
        y = df["sentiment"].values

        # 简单线性回归
        n = len(x)
        sum_x = np.sum(x)
        sum_y = np.sum(y)
        sum_xy = np.sum(x * y)
        sum_xx = np.sum(x * x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        r_squared = self._calculate_r_squared(x, y, slope)

        # 确定趋势方向
        threshold = 0.01  # 斜率阈值
        if slope > threshold:
            trend_dir = 1  # 上升
        elif slope < -threshold:
            trend_dir = -1  # 下降
        else:
            trend_dir = 0  # 平稳

        df["trend_direction"] = trend_dir
        df["trend_strength"] = r_squared

        return df

    def _calculate_r_squared(self, x: np.ndarray, y: np.ndarray, slope: float) -> float:
        """
        计算 R-squared 值

        Args:
            x: X values
            y: Y values
            slope: 斜率

        Returns:
            R-squared value
        """
        y_mean = np.mean(y)
        ss_tot = np.sum((y - y_mean) ** 2)

        if ss_tot == 0:
            return 1.0 if y[0] == y_mean else 0.0

        # 计算预测值
        y_pred = slope * x + np.mean(y) - slope * np.mean(x)
        ss_res = np.sum((y - y_pred) ** 2)

        r_squared = 1 - (ss_res / ss_tot)
        return max(0, min(1, r_squared))

    def export_to_csv(self, df: pd.DataFrame, output_path: str):
        """
        导出时间序列数据到 CSV

        Args:
            df: DataFrame 数据
            output_path: 输出文件路径
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path)
        print(f"Exported time series data to {output_path}")


# 方便使用的函数
def calculate_rolling_sentiment(
    commits: List[Dict],
    window_hours: int = 24
) -> pd.DataFrame:
    """
    快速计算滚动情感的便捷函数

    Args:
        commits: Commit 列表
        window_hours: 窗口大小（小时）

    Returns:
        情感时间序列 DataFrame
    """
    engine = SentimentTimeSeries()
    return engine.calculate_rolling_sentiment(commits, window_hours)
