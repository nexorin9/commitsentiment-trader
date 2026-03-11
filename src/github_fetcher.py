"""
GitHub Commit Fetcher Module

从 GitHub API 获取 commit 历史，支持分页和缓存。
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional

import requests

try:
    from .logger import log_error, log_warning, log_info
except ImportError:
    from logger import log_error, log_warning, log_info


class GitHubFetcher:
    """GitHub API 数据获取器"""

    def __init__(self, token: Optional[str] = None, cache_dir: str = "data"):
        """
        初始化 GitHub Fetcher

        Args:
            token: GitHub Personal Access Token
            cache_dir: 缓存目录路径
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.cache_dir = cache_dir
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CommitSentiment-Analyzer"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def _make_request(self, url: str, params: Dict = None) -> Dict:
        """
        发送 GitHub API 请求

        Args:
            url: API URL
            params: 查询参数

        Returns:
            JSON 响应数据
        """
        try:
            response = requests.get(url, headers=self.headers, params=params)

            # 处理 rate limit
            if response.status_code == 403:
                remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))

                if remaining == 0:
                    import time
                    wait_seconds = max(reset_time - int(datetime.now().timestamp()), 60)
                    log_warning(f"Rate limit reached. Waiting {wait_seconds} seconds...")
                    time.sleep(wait_seconds)
                    return self._make_request(url, params)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log_error(f"GitHub API request failed: {str(e)} | url={url}")
            raise
        except json.JSONDecodeError as e:
            log_error(f"Failed to parse JSON response: {str(e)} | url={url}")
            raise

    def fetch_commits(
        self,
        owner: str,
        repo: str,
        per_page: int = 30,
        max_commits: Optional[int] = None
    ) -> List[Dict]:
        """
        获取指定仓库的 commit 历史

        Args:
            owner: 仓库所有者
            repo: 仓库名
            per_page: 每页数量 (最大 100)
            max_commits: 最大获取 commit 数量

        Returns:
            Commit 列表
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": min(per_page, 100)}

        all_commits = []
        page = 1

        while True:
            params["page"] = page
            data = self._make_request(url, params)

            if not data:
                break

            all_commits.extend(data)

            # 检查是否达到最大数量
            if max_commits and len(all_commits) >= max_commits:
                break

            # 检查是否还有更多页面
            if len(data) < params["per_page"]:
                break

            page += 1

        return all_commits[:max_commits] if max_commits else all_commits

    def save_commits_to_cache(self, commits: List[Dict], owner: str, repo: str):
        """
        将 commits 保存到缓存文件

        Args:
            commits: Commit 列表
            owner: 仓库所有者
            repo: 仓库名
        """
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

            log_info(f"Saved {len(commits)} commits to cache", filepath=filepath)
        except IOError as e:
            log_error(f"Failed to save commits to cache: {str(e)}", owner=owner, repo=repo)
            raise

    def load_commits_from_cache(self, owner: str, repo: str) -> Optional[List[Dict]]:
        """
        从缓存加载 commits

        Args:
            owner: 仓库所有者
            repo: 仓库名

        Returns:
            Commit 列表，如果缓存不存在则返回 None
        """
        try:
            filename = f"{owner}_{repo}_commits.json"
            filepath = os.path.join(self.cache_dir, filename)

            if not os.path.exists(filepath):
                return None

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            log_info(f"Loaded {len(data.get('commits', []))} commits from cache", owner=owner, repo=repo)
            return data.get("commits", [])
        except json.JSONDecodeError as e:
            log_error(f"Failed to load commits from cache: {str(e)}", filepath=filepath)
            return None
        except IOError as e:
            log_error(f"IO error while loading cache: {str(e)}", filepath=filepath)
            return None

    def get_commit_details(self, owner: str, repo: str, sha: str) -> Dict:
        """
        获取单个 commit 的详细信息

        Args:
            owner: 仓库所有者
            repo: 仓库名
            sha: Commit SHA

        Returns:
            Commit 详细信息
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits/{sha}"
        return self._make_request(url)

    def fetch_commits_with_cache(
        self,
        owner: str,
        repo: str,
        force_refresh: bool = False,
        max_commits: Optional[int] = None
    ) -> List[Dict]:
        """
        带缓存的 commits 获取

        Args:
            owner: 仓库所有者
            repo: 仓库名
            force_refresh: 是否强制刷新缓存
            max_commits: 最大获取 commit 数量

        Returns:
            Commit 列表
        """
        if not force_refresh:
            cached = self.load_commits_from_cache(owner, repo)
            if cached is not None:
                return cached

        commits = self.fetch_commits(owner, repo, max_commits=max_commits)
        self.save_commits_to_cache(commits, owner, repo)

        return commits


# 方便使用的函数
def fetch_commits(owner: str, repo: str, token: Optional[str] = None) -> List[Dict]:
    """
    快速获取 commits 的便捷函数

    Args:
        owner: 仓库所有者
        repo: 仓库名
        token: GitHub Token (可选)

    Returns:
        Commit 列表
    """
    try:
        fetcher = GitHubFetcher(token=token)
        return fetcher.fetch_commits(owner, repo)
    except Exception as e:
        log_error(f"Failed to fetch commits: {str(e)}", owner=owner, repo=repo)
        return []
