"""
GitHub Commit Fetcher - Async Version

使用 asyncio 和 aiohttp 实现并发请求，大幅提升 API 获取性能。
"""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from .logger import log_error, log_warning, log_info
except ImportError:
    try:
        from logger import log_error, log_warning, log_info
    except ImportError:
        import logging
        def log_error(msg, **kwargs): logging.error(f"{msg} {kwargs}")
        def log_warning(msg, **kwargs): logging.warning(f"{msg} {kwargs}")
        def log_info(msg, **kwargs): logging.info(f"{msg} {kwargs}")


class AsyncGitHubFetcher:
    """
    异步 GitHub API 获取器
    使用 aiohttp 实现并发请求，显著提升性能
    """

    def __init__(
        self,
        token: Optional[str] = None,
        cache_dir: str = "data",
        max_concurrent_requests: int = 5,
        request_timeout: int = 30
    ):
        """
        初始化异步 Fetcher

        Args:
            token: GitHub Personal Access Token
            cache_dir: 缓存目录路径
            max_concurrent_requests: 最大并发请求数
            request_timeout: 请求超时时间（秒）
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.cache_dir = cache_dir
        self.base_url = "https://api.github.com"
        self.max_concurrent = max_concurrent_requests
        self.timeout = request_timeout

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CommitSentiment-Analyzer-Async"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_remaining = None
        self._rate_limit_reset = None

    async def __aenter__(self):
        """Async context manager entry"""
        if AIOHTTP_AVAILABLE:
            self._session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session and not self._session.closed:
            await self._session.close()

    def _check_cache(self, owner: str, repo: str) -> Optional[List[Dict]]:
        """检查缓存（同步方法，供外部调用）"""
        try:
            filename = f"{owner}_{repo}_commits.json"
            filepath = os.path.join(self.cache_dir, filename)

            if not os.path.exists(filepath):
                return None

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            log_info(f"Loaded {len(data.get('commits', []))} commits from cache")
            return data.get("commits", [])
        except Exception as e:
            log_error(f"Failed to load from cache: {str(e)}")
            return None

    def _save_to_cache(self, commits: List[Dict], owner: str, repo: str):
        """保存到缓存（同步方法，供外部调用）"""
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            filename = f"{owner}_{repo}_commits.json"
            filepath = os.path.join(self.cache_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "owner": owner,
                    "repo": repo,
                    "timestamp": datetime.now().isoformat(),
                    "commits": commits
                }, f, indent=2, ensure_ascii=False)

            log_info(f"Saved {len(commits)} commits to cache")
        except Exception as e:
            log_error(f"Failed to save to cache: {str(e)}")

    async def _check_rate_limit(self, session: aiohttp.ClientSession):
        """检查 rate limit 并等待"""
        if self._rate_limit_remaining is not None and self._rate_limit_remaining <= 10:
            if self._rate_limit_reset:
                now = datetime.now().timestamp()
                wait_time = self._rate_limit_reset - now
                if wait_time > 0:
                    log_warning(f"Rate limit approaching. Waiting {wait_time:.0f}s...")
                    await asyncio.sleep(min(wait_time + 5, 60))

    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: Dict = None,
        max_retries: int = 3
    ) -> Dict:
        """
        异步发送请求

        Args:
            session: aiohttp session
            url: API URL
            params: 查询参数
            max_retries: 最大重试次数

        Returns:
            JSON 响应数据
        """
        for attempt in range(max_retries):
            try:
                async with asyncio.timeout(self.timeout):
                    async with session.get(url, params=params) as response:
                        # 解析 rate limit headers
                        self._rate_limit_remaining = int(
                            response.headers.get("X-RateLimit-Remaining", "5000")
                        )
                        self._rate_limit_reset = int(
                            response.headers.get("X-RateLimit-Reset", "0")
                        )

                        if response.status == 403:
                            reset_time = int(self._rate_limit_reset)
                            now = datetime.now().timestamp()
                            wait_seconds = max(reset_time - now, 60)

                            if self._rate_limit_remaining <= 0:
                                log_warning(f"Rate limit reached. Waiting {wait_seconds:.0f}s...")
                                await asyncio.sleep(wait_seconds)
                                continue

                        response.raise_for_status()
                        return await response.json()

            except asyncio.TimeoutError:
                log_warning(f"Request timeout, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

            except aiohttp.ClientError as e:
                log_error(f"HTTP error: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise

        raise Exception(f"Request failed after {max_retries} retries")

    async def _fetch_page(
        self,
        session: aiohttp.ClientSession,
        owner: str,
        repo: str,
        page: int,
        per_page: int = 100
    ) -> Tuple[List[Dict], bool]:
        """
        获取单页 commits

        Returns:
            (commits 列表, 是否还有更多页面)
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": per_page, "page": page}

        try:
            data = await self._make_request(session, url, params)

            if not isinstance(data, list):
                return [], False

            # 检查是否到达末尾
            has_more = len(data) >= per_page
            return data, has_more

        except Exception as e:
            log_error(f"Failed to fetch page {page}: {str(e)}")
            return [], False

    async def fetch_commits_async(
        self,
        owner: str,
        repo: str,
        per_page: int = 100,
        max_commits: Optional[int] = None
    ) -> List[Dict]:
        """
        异步获取指定仓库的 commit 历史（无缓存）

        Args:
            owner: 仓库所有者
            repo: 仓库名
            per_page: 每页数量 (最大 100)
            max_commits: 最大获取 commit 数量

        Returns:
            Commit 列表
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError(
                "aiohttp is required for async operations. "
                "Install with: pip install aiohttp"
            )

        all_commits = []
        page = 1
        per_page = min(per_page, 100)

        async with aiohttp.ClientSession(headers=self.headers) as session:
            while True:
                await self._check_rate_limit(session)

                commits, has_more = await self._fetch_page(
                    session, owner, repo, page, per_page
                )

                if not commits:
                    break

                all_commits.extend(commits)

                # 检查是否达到最大数量
                if max_commits and len(all_commits) >= max_commits:
                    break

                # 检查是否还有更多页面
                if not has_more:
                    break

                page += 1

        return all_commits[:max_commits] if max_commits else all_commits

    async def fetch_commits_batch_async(
        self,
        repositories: List[Tuple[str, str]],
        max_commits_per_repo: Optional[int] = None
    ) -> Dict[Tuple[str, str], List[Dict]]:
        """
        并发获取多个仓库的 commits（并发请求）

        Args:
            repositories: 仓库列表 [(owner, repo), ...]
            max_commits_per_repo: 每个仓库的最大 commits 数

        Returns:
            { (owner, repo): commits_list, ... }
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required")

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def fetch_with_semaphore(owner: str, repo: str):
            async with semaphore:
                try:
                    commits = await self.fetch_commits_async(
                        owner, repo, max_commits=max_commits_per_repo
                    )
                    return (owner, repo), commits, None
                except Exception as e:
                    return (owner, repo), [], str(e)

        # 创建所有任务
        tasks = [
            fetch_with_semaphore(owner, repo)
            for owner, repo in repositories
        ]

        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        output = {}
        for result in results:
            if isinstance(result, Exception):
                log_error(f"Task failed: {str(result)}")
                continue

            if isinstance(result, tuple) and len(result) >= 3:
                key, commits, error = result
                if error:
                    log_error(f"Failed to fetch {key[0]}/{key[1]}: {error}")
                else:
                    log_info(f"Fetched {len(commits)} commits from {key[0]}/{key[1]}")
                output[key] = commits

        return output

    async def fetch_commits_with_cache_async(
        self,
        owner: str,
        repo: str,
        force_refresh: bool = False,
        max_commits: Optional[int] = None
    ) -> List[Dict]:
        """
        异步带缓存的 commits 获取

        Args:
            owner: 仓库所有者
            repo: 仓库名
            force_refresh: 是否强制刷新缓存
            max_commits: 最大获取 commit 数量

        Returns:
            Commit 列表
        """
        # Step 1: 检查缓存
        if not force_refresh:
            cached = self._check_cache(owner, repo)
            if cached is not None:
                return cached

        # Step 2: 获取数据
        commits = await self.fetch_commits_async(
            owner, repo, max_commits=max_commits
        )

        # Step 3: 保存到缓存
        if commits:
            self._save_to_cache(commits, owner, repo)

        return commits

    def fetch_commits_with_cache(
        self,
        owner: str,
        repo: str,
        force_refresh: bool = False,
        max_commits: Optional[int] = None
    ) -> List[Dict]:
        """
        同步包装方法，方便外部调用

        Args:
            owner: 仓库所有者
            repo: 仓库名
            force_refresh: 是否强制刷新缓存
            max_commits: 最大获取 commit 数量

        Returns:
            Commit 列表
        """
        if not AIOHTTP_AVAILABLE:
            # 优雅降级到同步版本
            log_warning("aiohttp not available, using sync fetcher")
            from .github_fetcher import GitHubFetcher
            fetcher = GitHubFetcher(token=self.token, cache_dir=self.cache_dir)
            return fetcher.fetch_commits_with_cache(
                owner, repo, force_refresh, max_commits
            )

        return asyncio.run(
            self.fetch_commits_with_cache_async(
                owner, repo, force_refresh, max_commits
            )
        )


# 向后兼容的便捷函数
def fetch_commits_async(
    owner: str,
    repo: str,
    token: Optional[str] = None,
    max_concurrent: int = 5
) -> List[Dict]:
    """
    快速异步获取 commits（异步版本）

    Args:
        owner: 仓库所有者
        repo: 仓库名
        token: GitHub Token
        max_concurrent: 最大并发数

    Returns:
        Commit 列表
    """
    if not AIOHTTP_AVAILABLE:
        from .github_fetcher import fetch_commits
        return fetch_commits(owner, repo, token)

    fetcher = AsyncGitHubFetcher(token=token, max_concurrent_requests=max_concurrent)
    return asyncio.run(fetcher.fetch_commits_async(owner, repo))


def fetch_repos_batch_async(
    repositories: List[Tuple[str, str]],
    token: Optional[str] = None,
    max_concurrent: int = 5
) -> Dict[Tuple[str, str], List[Dict]]:
    """
    批量并发获取多个仓库的 commits

    Args:
        repositories: 仓库列表
        token: GitHub Token
        max_concurrent: 最大并发数

    Returns:
        { (owner, repo): commits, ... }
    """
    if not AIOHTTP_AVAILABLE:
        from .github_fetcher import fetch_commits
        return {
            (owner, repo): fetch_commits(owner, repo, token)
            for owner, repo in repositories
        }

    fetcher = AsyncGitHubFetcher(token=token, max_concurrent_requests=max_concurrent)
    return asyncio.run(fetcher.fetch_commits_batch_async(repositories))
