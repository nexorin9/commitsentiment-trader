"""
Optimized Data Pipeline

优化的数据预处理流水线，使用并发请求和批量处理提升性能。
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Handle both relative and absolute imports
try:
    from .github_fetcher_async import AsyncGitHubFetcher
    ASYNC_AVAILABLE = True
except ImportError:
    try:
        from github_fetcher_async import AsyncGitHubFetcher
        ASYNC_AVAILABLE = True
    except ImportError:
        ASYNC_AVAILABLE = False
        AsyncGitHubFetcher = None

try:
    from .sentiment_analyzer import CommitSentimentAnalyzer
except ImportError:
    try:
        from sentiment_analyzer import CommitSentimentAnalyzer
    except ImportError:
        sys.path.insert(0, os.path.dirname(__file__))
        from sentiment_analyzer import CommitSentimentAnalyzer

try:
    from .time_series import SentimentTimeSeries
except ImportError:
    try:
        from time_series import SentimentTimeSeries
    except ImportError:
        sys.path.insert(0, os.path.dirname(__file__))
        from time_series import SentimentTimeSeries

try:
    from .signal_generator import SignalGenerator
except ImportError:
    try:
        from signal_generator import SignalGenerator
    except ImportError:
        sys.path.insert(0, os.path.dirname(__file__))
        from signal_generator import SignalGenerator

try:
    from .logger import log_error, log_warning, log_info
except ImportError:
    try:
        from logger import log_error, log_warning, log_info
    except ImportError:
        sys.path.insert(0, os.path.dirname(__file__))
        from logger import log_error, log_warning, log_info


class OptimizedDataPipeline:
    """
    优化的数据预处理流水线

    主要优化点：
    1. 使用 async/await 并发获取 GitHub API 数据
    2. 批量处理 commits 进行情感分析
    3. 优化的缓存策略
    4. 并发处理多个仓库
    """

    def __init__(
        self,
        token: Optional[str] = None,
        cache_dir: str = "data",
        use_async: bool = True,
        max_workers: int = 4
    ):
        """
        初始化优化流水线

        Args:
            token: GitHub API Token
            cache_dir: 缓存目录路径
            use_async: 是否使用异步获取（需要 aiohttp）
            max_workers: 线程池最大工作线程数
        """
        self.use_async = use_async and ASYNC_AVAILABLE
        self.max_workers = max_workers

        if self.use_async:
            self.github_fetcher = AsyncGitHubFetcher(
                token=token,
                cache_dir=cache_dir
            )
        else:
            from .github_fetcher import GitHubFetcher
            self.github_fetcher = GitHubFetcher(token=token, cache_dir=cache_dir)

        self.sentiment_analyzer = CommitSentimentAnalyzer()
        self.time_series_engine = SentimentTimeSeries()

    def _process_single_commit(self, commit: Dict) -> Optional[Dict]:
        """
        处理单个 commit
        """
        try:
            if "commit" not in commit or "message" not in commit["commit"]:
                return None

            message = commit["commit"]["message"]
            sentiment = self.sentiment_analyzer.analyze_commit(message)

            # 提取时间戳
            date_str = None
            if "commit" in commit and "committer" in commit["commit"]:
                date_str = commit["commit"]["committer"].get("date")
            elif "commit" in commit and "author" in commit["commit"]:
                date_str = commit["commit"]["author"].get("date")

            timestamp = None
            if date_str:
                try:
                    timestamp = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    timestamp = None

            return {
                "message": message,
                "sentiment": sentiment,
                "timestamp": timestamp,
                "sha": commit.get("sha", "")
            }
        except Exception as e:
            log_error(f"Error processing commit: {str(e)}")
            return None

    def _batch_analyze_commits(self, messages: List[str]) -> List[Dict]:
        """
        批量分析情感（使用列表推导式优化）
        """
        return self.sentiment_analyzer.analyze_commits(messages)

    def fetch_and_process_repo(
        self,
        owner: str,
        repo: str,
        max_commits: Optional[int] = None
    ) -> Dict:
        """
        处理单个仓库（优化版本）

        Args:
            owner: 仓库所有者
            repo: 仓库名
            max_commits: 最大处理 commit 数量

        Returns:
            处理结果字典
        """
        print(f"Processing {owner}/{repo}...")

        # Step 1: 获取 commits（异步或同步）
        print("Fetching commits...")
        if self.use_async:
            try:
                import asyncio
                commits = asyncio.run(
                    self.github_fetcher.fetch_commits_with_cache_async(
                        owner, repo, max_commits=max_commits
                    )
                )
            except Exception as e:
                log_error(f"Async fetch failed, falling back to sync: {str(e)}")
                commits = self.github_fetcher.fetch_commits_with_cache(
                    owner, repo, max_commits=max_commits
                )
        else:
            commits = self.github_fetcher.fetch_commits_with_cache(
                owner, repo, max_commits=max_commits
            )

        print(f"Fetched {len(commits)} commits")

        if not commits:
            return {"error": "No commits found"}

        # Step 2: 提取消息（使用列表推导式）
        messages = [
            c.get("commit", {}).get("message", "")
            for c in commits
            if "commit" in c and "message" in c.get("commit", {})
        ]
        print(f"Extracted {len(messages)} messages")

        # Step 3: 批量情感分析
        print("Analyzing sentiment...")
        sentiments = self._batch_analyze_commits(messages)
        print(f"Analyzed {len(sentiments)} messages")

        # Step 4: 构建时间序列
        print("Building time series...")
        time_series_df = self.time_series_engine.calculate_rolling_sentiment(commits)

        # Step 5: 生成信号
        print("Generating signals...")
        data_dict = {
            "timestamps": [str(ts) for ts in time_series_df.index],
            "sentiments": time_series_df["sentiment"].tolist()
        }
        signal_gen = SignalGenerator(threshold=0.3)
        signals = signal_gen.generate_signals(data_dict)

        # 计算统计信息（使用生成器表达式优化）
        if sentiments:
            compound_scores = [s.get("compound", 0) for s in sentiments]
            avg_sentiment = sum(compound_scores) / len(compound_scores)
            positive_count = sum(1 for s in compound_scores if s > 0.3)
            positive_ratio = positive_count / len(compound_scores)
        else:
            avg_sentiment = 0.0
            positive_ratio = 0.0

        return {
            "owner": owner,
            "repo": repo,
            "commits_count": len(commits),
            "sentiment_analysis": {
                "messages_count": len(messages),
                "avg_sentiment": round(avg_sentiment, 4),
                "positive_ratio": round(positive_ratio, 4)
            },
            "time_series": data_dict,
            "signals": signals,
            "timestamp": datetime.now().isoformat()
        }

    def fetch_and_process_concurrent(
        self,
        repositories: List[Tuple[str, str]],
        max_commits_per_repo: Optional[int] = None
    ) -> List[Dict]:
        """
        并发处理多个仓库（多线程）

        Args:
            repositories: 仓库列表 [(owner, repo), ...]
            max_commits_per_repo: 每个仓库的最大 commits 数

        Returns:
            处理结果列表
        """
        results = []
        total_repos = len(repositories)

        print(f"Processing {total_repos} repositories concurrently...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_repo = {
                executor.submit(
                    self.fetch_and_process_repo,
                    owner, repo, max_commits_per_repo
                ): (owner, repo)
                for owner, repo in repositories
            }

            # 收集结果
            completed = 0
            for future in as_completed(future_to_repo):
                owner, repo = future_to_repo[future]
                try:
                    result = future.result()
                    if "error" not in result:
                        results.append(result)
                        print(f"[{completed + 1}/{total_repos}] Completed {owner}/{repo}")
                    else:
                        print(f"[{completed + 1}/{total_repos}] Failed {owner}/{repo}: {result['error']}")
                except Exception as e:
                    print(f"[{completed + 1}/{total_repos}] Error {owner}/{repo}: {e}")
                    results.append({"owner": owner, "repo": repo, "error": str(e)})

                completed += 1

        return results

    def process_multiple_repos(
        self,
        repos: List[Tuple[str, str]]
    ) -> List[Dict]:
        """
        批量处理多个仓库（兼容旧接口）

        Args:
            repos: 仓库列表

        Returns:
            处理结果列表
        """
        return self.fetch_and_process_concurrent(repos)


# 便利的快速函数
def process_repo_optimized(
    owner: str,
    repo: str,
    token: Optional[str] = None,
    use_async: bool = True
) -> Dict:
    """
    快速处理单个仓库的便捷函数

    Args:
        owner: 仓库所有者
        repo: 仓库名
        token: GitHub Token
        use_async: 是否使用异步

    Returns:
        处理结果字典
    """
    pipeline = OptimizedDataPipeline(token=token, use_async=use_async)
    return pipeline.fetch_and_process_repo(owner, repo)


def process_repos_batch_optimized(
    repositories: List[Tuple[str, str]],
    token: Optional[str] = None,
    max_workers: int = 4
) -> List[Dict]:
    """
    快速批量处理仓库的便捷函数

    Args:
        repositories: 仓库列表
        token: GitHub Token
        max_workers: 最大工作线程数

    Returns:
        处理结果列表
    """
    pipeline = OptimizedDataPipeline(token=token, max_workers=max_workers)
    return pipeline.fetch_and_process_concurrent(repositories)
