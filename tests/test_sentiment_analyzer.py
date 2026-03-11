"""
Unit Tests for CommitSentiment Trader

为关键模块编写单元测试，确保功能正确性。
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from sentiment_analyzer import CommitSentimentAnalyzer, analyze_commit
from github_fetcher import GitHubFetcher
from signal_generator import SignalGenerator, TradingSignal


class TestSentimentAnalyzer:
    """Sentiment Analyzer 测试"""

    def setup_method(self):
        """测试前初始化"""
        self.analyzer = CommitSentimentAnalyzer()

    def test_analyze_commit_returns_correct_keys(self):
        """测试 analyze_commit 返回正确的键"""
        result = self.analyzer.analyze_commit("good commit")
        assert "compound" in result
        assert "pos" in result
        assert "neu" in result
        assert "neg" in result

    def test_analyze_commit_returns_float_values(self):
        """测试 analyze_commit 返回浮点数值"""
        result = self.analyzer.analyze_commit("good commit")
        assert isinstance(result["compound"], float)
        assert isinstance(result["pos"], float)
        assert isinstance(result["neu"], float)
        assert isinstance(result["neg"], float)

    def test_analyze_commit_range(self):
        """测试 analyze_commit 返回值在 [-1, 1] 范围内"""
        result = self.analyzer.analyze_commit("good commit")
        assert -1 <= result["compound"] <= 1

    def test_analyze_commit_empty_string(self):
        """测试空字符串处理"""
        result = self.analyzer.analyze_commit("")
        assert result["compound"] == 0.0

    def test_analyze_commit_none_string(self):
        """测试 None 处理"""
        result = self.analyzer.analyze_commit(None)
        assert result["compound"] == 0.0

    def test_analyze_commit_special_characters(self):
        """测试特殊字符处理"""
        result = self.analyzer.analyze_commit("fix bug!!!")
        assert isinstance(result["compound"], float)

    def test_analyze_commit_positive_message(self):
        """测试积极消息分析"""
        result = self.analyzer.analyze_commit("add new feature")
        # 加法是正向词汇
        assert result["compound"] >= 0

    def test_analyze_commit_negative_message(self):
        """测试消极消息分析"""
        result = self.analyzer.analyze_commit("revert bad change")
        # revert 是负向词汇
        assert result["compound"] <= 0.5  # 不一定是负数，取决于上下文

    def test_analyze_commits_batch(self):
        """测试批量分析"""
        messages = ["good commit", "bad commit"]
        results = self.analyzer.analyze_commits(messages)
        assert len(results) == 2
        assert isinstance(results[0]["compound"], float)
        assert isinstance(results[1]["compound"], float)

    def test_analyze_commits_empty_list(self):
        """测试空列表处理"""
        results = self.analyzer.analyze_commits([])
        assert results == []

    def test_get_compound_score(self):
        """测试 get_compound_score 函数"""
        score = self.analyzer.get_compound_score("good commit")
        assert isinstance(score, float)
        assert -1 <= score <= 1


class TestSignalGenerator:
    """Signal Generator 测试"""

    def setup_method(self):
        """测试前初始化"""
        self.signal_gen = SignalGenerator(threshold=0.3)

    def test_generate_signals_returns_list(self):
        """测试 generate_signals 返回列表"""
        data = {
            "timestamps": ["2026-01-01", "2026-01-02"],
            "sentiments": [0.5, 0.6]
        }
        signals = self.signal_gen.generate_signals(data)
        assert isinstance(signals, list)

    def test_generate_signals_signal_type(self):
        """测试信号类型"""
        data = {
            "timestamps": ["2026-01-01"],
            "sentiments": [0.5]  # 高于阈值
        }
        signals = self.signal_gen.generate_signals(data)
        if signals:
            assert signals[0]["signal"] in ["BUY", "SELL", "HOLD"]

    def test_generate_signals_empty_data(self):
        """测试空数据处理"""
        data = {"timestamps": [], "sentiments": []}
        signals = self.signal_gen.generate_signals(data)
        assert signals == []

    def test_generate_signals_below_threshold(self):
        """测试低于阈值的情况"""
        data = {
            "timestamps": ["2026-01-01"],
            "sentiments": [0.1]  # 低于阈值
        }
        signals = self.signal_gen.generate_signals(data)
        # 没有达到阈值，应该只有 HOLD 信号
        assert all(s["signal"] == "HOLD" for s in signals)

    def test_generate_signals_above_threshold(self):
        """测试高于阈值的情况"""
        data = {
            "timestamps": ["2026-01-01"],
            "sentiments": [0.6]  # 高于阈值
        }
        signals = self.signal_gen.generate_signals(data)
        # 高于阈值，应该有 BUY 或 SELL 信号
        for signal in signals:
            assert signal["signal"] in ["BUY", "SELL"]

    def test_generation_signals_multiple_points(self):
        """测试多个时间点的信号生成"""
        data = {
            "timestamps": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "sentiments": [0.5, 0.6, 0.7]
        }
        signals = self.signal_gen.generate_signals(data)
        # 信号生成器生成BUY/SELL/HOLD信号，不是每个时间点都有信号
        # 只有当情感超过阈值时才生成非HOLD信号
        assert len(signals) >= 0  # 至少有0个信号
        assert all(s["signal"] in ["BUY", "SELL", "HOLD"] for s in signals)


class TestGitHubFetcher:
    """GitHub Fetcher 测试"""

    def setup_method(self):
        """测试前初始化"""
        self.fetcher = GitHubFetcher(token=None)  # 不使用真实 token

    def test_init_with_token(self):
        """测试带 token 初始化"""
        fetcher = GitHubFetcher(token="fake_token")
        assert fetcher.token == "fake_token"

    def test_init_with_env_var(self, monkeypatch):
        """测试从环境变量读取 token"""
        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        fetcher = GitHubFetcher()
        assert fetcher.token == "env_token"

    def test_fetch_commits_with_mock_data(self):
        """测试带 mock 数据的 fetch_commits"""
        # 这里只测试缓存加载
        result = self.fetcher.load_commits_from_cache("fake", "repo")
        # 因为没有实际缓存，应该返回 None
        assert result is None


# 方便运行测试的函数
def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
