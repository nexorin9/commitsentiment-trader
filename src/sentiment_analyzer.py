"""
Commit Sentiment Analyzer Module

基于 VADER 的 commit 情感分析模块，处理短文本特例。
"""

import re
from typing import Dict, List, Optional

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

try:
    from .logger import log_error, log_warning
except ImportError:
    from logger import log_error, log_warning


class CommitSentimentAnalyzer:
    """Commit 情感分析器"""

    def __init__(self):
        """
        初始化 VADER 分析器并添加针对 commit 的自定义词典
        """
        self.analyzer = SentimentIntensityAnalyzer()

        # GitHub commit 特定的词汇表
        # 这些词在代码提交中常见但不在 VADER 默认词典中
        custom_words = {
            # 正向词汇 (表示改进、修复)
            "fix": 2.5,
            "fixed": 2.5,
            "bug": -1.0,  # 提到 bug 通常意味着需要修复，情感稍负
            "bugs": -1.0,
            "patch": 1.5,
            "improve": 2.0,
            "improved": 2.0,
            "add": 1.5,
            "added": 1.5,
            "new": 1.5,
            "feature": 2.0,
            "features": 2.0,
            "update": 1.0,
            "updated": 1.0,
            "refactor": 0.5,
            "rename": 0.3,
            "remove": -0.5,
            "removed": -0.5,
            "delete": -0.5,
            "deleted": -0.5,
            "optimize": 1.5,
            "optimized": 1.5,
            "perf": 1.5,
            "performance": 1.5,
            "test": 0.5,
            "tests": 0.5,
            "ci": 0.3,
            "build": 0.5,
            "release": 1.0,
            "merge": 0.2,
            "revert": -1.0,
            "hotfix": 2.0,  # 紧急修复通常是正面的
            "security": -0.5,  # 安全问题本身是负面的，但修复是正面的
        }

        # 添加自定义词汇到分析器 lexicon
        for word, score in custom_words.items():
            self.analyzer.lexicon[word] = score

    def preprocess_message(self, message: str) -> str:
        """
        预处理 commit message

        Args:
            message: 原始 commit message

        Returns:
            处理后的消息
        """
        if not message or not isinstance(message, str):
            return ""

        # 移除特殊字符但保留基本标点
        message = re.sub(r"[^\w\s.,!?-]", " ", message)

        # 标准化大小写（保留全大写的强调词）
        message = " ".join(
            word if word.isupper() and len(word) > 1 else word.lower()
            for word in message.split()
        )

        return message.strip()

    def analyze_commit(self, message: str) -> Dict[str, float]:
        """
        分析单个 commit message 的情感

        Args:
            message: Commit message

        Returns:
            包含 sentiment scores 的字典
            - compound: 综合情绪分数 (-1 到 +1)
            - pos: 正向分数
            - neu: 中性分数
            - neg: 负向分数
        """
        try:
            processed = self.preprocess_message(message)

            if not processed:
                return {
                    "compound": 0.0,
                    "pos": 0.0,
                    "neu": 0.0,
                    "neg": 0.0
                }

            scores = self.analyzer.polarity_scores(processed)
            return scores
        except Exception as e:
            log_error(f"Failed to analyze commit sentiment: {str(e)}")
            return {
                "compound": 0.0,
                "pos": 0.0,
                "neu": 0.0,
                "neg": 0.0
            }

    def analyze_commits(self, messages: List[str]) -> List[Dict]:
        """
        批量分析多个 commit message

        Args:
            messages: Commit message 列表

        Returns:
            情感分析结果列表
        """
        results = []
        for i, msg in enumerate(messages):
            try:
                result = self.analyze_commit(msg)
                results.append(result)
            except Exception as e:
                log_error(f"Failed to analyze commit at index {i}: {str(e)}")
                results.append({
                    "compound": 0.0,
                    "pos": 0.0,
                    "neu": 0.0,
                    "neg": 0.0
                })
        return results

    def get_compound_score(self, message: str) -> float:
        """
        获取 commit 的 compound score

        Args:
            message: Commit message

        Returns:
            Compound score (-1 到 +1)
        """
        scores = self.analyze_commit(message)
        return scores["compound"]


# 方便使用的函数
def analyze_commit(message: str) -> Dict[str, float]:
    """
    快速分析单个 commit 的便捷函数

    Args:
        message: Commit message

    Returns:
        情感分数字典
    """
    try:
        analyzer = CommitSentimentAnalyzer()
        return analyzer.analyze_commit(message)
    except Exception as e:
        log_error(f"Failed to analyze commit: {str(e)}")
        return {
            "compound": 0.0,
            "pos": 0.0,
            "neu": 0.0,
            "neg": 0.0
        }


def analyze_commits_batch(messages: List[str]) -> List[Dict]:
    """
    批量分析 commit 的便捷函数

    Args:
        messages: Commit message 列表

    Returns:
        情感分数列表
    """
    try:
        analyzer = CommitSentimentAnalyzer()
        return analyzer.analyze_commits(messages)
    except Exception as e:
        log_error(f"Failed to analyze commits batch: {str(e)}")
        return [{"compound": 0.0, "pos": 0.0, "neu": 0.0, "neg": 0.0} for _ in messages]
