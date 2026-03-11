"""
Data Preprocessing Pipeline

数据清洗和预处理流水线，整合所有数据源。
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    from .github_fetcher import GitHubFetcher
except ImportError:
    from github_fetcher import GitHubFetcher

try:
    from .sentiment_analyzer import CommitSentimentAnalyzer
except ImportError:
    from sentiment_analyzer import CommitSentimentAnalyzer

try:
    from .time_series import SentimentTimeSeries
except ImportError:
    from time_series import SentimentTimeSeries

try:
    from .signal_generator import SignalGenerator
except ImportError:
    from signal_generator import SignalGenerator

try:
    from .logger import log_error, log_warning, log_info
except ImportError:
    from logger import log_error, log_warning, log_info


class DataPipeline:
    """数据预处理流水线"""

    def __init__(
        self,
        token: Optional[str] = None,
        cache_dir: str = "data"
    ):
        """
        初始化数据流水线

        Args:
            token: GitHub API Token
            cache_dir: 缓存目录路径
        """
        self.github_fetcher = GitHubFetcher(token=token, cache_dir=cache_dir)
        self.sentiment_analyzer = CommitSentimentAnalyzer()
        self.time_series_engine = SentimentTimeSeries()

    def fetch_and_process_repo(
        self,
        owner: str,
        repo: str,
        max_commits: Optional[int] = None
    ) -> Dict:
        """
        处理单个仓库的完整流程

        Args:
            owner: 仓库所有者
            repo: 仓库名
            max_commits: 最大处理 commit 数量

        Returns:
            包含所有处理结果的字典
        """
        print(f"Processing {owner}/{repo}...")

        # Step 1: 获取 commits
        print("Fetching commits...")
        commits = self.github_fetcher.fetch_commits_with_cache(
            owner, repo, max_commits=max_commits
        )
        print(f"Fetched {len(commits)} commits")

        if not commits:
            return {"error": "No commits found"}

        # Step 2: 分析情感
        print("Analyzing sentiment...")
        messages = []
        for commit in commits:
            msg = self._extract_commit_message(commit)
            if msg:
                messages.append(msg)

        sentiments = self.sentiment_analyzer.analyze_commits(messages)
        print(f"Analyzed {len(sentiments)} commit messages")

        # Step 3: 构建时间序列
        print("Building time series...")
        time_series_df = self.time_series_engine.calculate_rolling_sentiment(commits)

        # 准备数据字典
        data_dict = {
            "timestamps": [str(ts) for ts in time_series_df.index],
            "sentiments": time_series_df["sentiment"].tolist()
        }

        # Step 4: 生成信号
        print("Generating signals...")
        signal_gen = SignalGenerator(threshold=0.3)
        signals = signal_gen.generate_signals(data_dict)

        return {
            "owner": owner,
            "repo": repo,
            "commits_count": len(commits),
            "sentiment_analysis": {
                "messages_count": len(messages),
                "avg_sentiment": sum(s["compound"] for s in sentiments) / len(sentiments) if sentiments else 0,
                "positive_ratio": sum(1 for s in sentiments if s["compound"] > 0.3) / len(sentiments) if sentiments else 0
            },
            "time_series": data_dict,
            "signals": signals,
            "timestamp": datetime.now().isoformat()
        }

    def _extract_commit_message(self, commit: Dict) -> Optional[str]:
        """
        从 commit 数据中提取 message

        Args:
            commit: GitHub API 返回的 commit 数据

        Returns:
            Commit message 字符串
        """
        try:
            if "commit" in commit and "message" in commit["commit"]:
                return commit["commit"]["message"]
            elif "commit" in commit and "title" in commit["commit"]:
                return commit["commit"]["title"]
            else:
                return str(commit.get("sha", ""))[:10]
        except (KeyError, TypeError):
            return ""

    def process_multiple_repos(
        self,
        repos: List[Tuple[str, str]]
    ) -> List[Dict]:
        """
        批量处理多个仓库

        Args:
            repos: 仓库列表，每个元素为 (owner, repo) 元组

        Returns:
            处理结果列表
        """
        results = []
        for owner, repo in repos:
            try:
                result = self.fetch_and_process_repo(owner, repo)
                if "error" not in result:
                    results.append(result)
                print(f"Completed {owner}/{repo}\n")
            except Exception as e:
                print(f"Error processing {owner}/{repo}: {e}")
                results.append({"owner": owner, "repo": repo, "error": str(e)})

        return results


# 方便使用的函数
def fetch_and_process_repo(owner: str, repo: str) -> Dict:
    """
    处理单个仓库的便捷函数

    Args:
        owner: 仓库所有者
        repo: 仓库名

    Returns:
        处理结果字典
    """
    pipeline = DataPipeline()
    return pipeline.fetch_and_process_repo(owner, repo)
