"""
Configuration System

实现配置管理系统，支持 JSON/YAML 格式的项目配置。
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class RepoConfig:
    """仓库配置"""
    owner: str
    repo: str
    days: int = 30
    max_commits: Optional[int] = None


@dataclass
class SymbolConfig:
    """股票配置"""
    symbol: str
    initial_capital: float = 10000.0


@dataclass
class ThresholdConfig:
    """阈值配置"""
    sentiment_threshold: float = 0.3
    min_hold_hours: int = 24


@dataclass
class WindowConfig:
    """时间窗口配置"""
    window_hours: int = 24
    trend_window_hours: int = 48


@dataclass
class PathConfig:
    """路径配置"""
    data_dir: str = "data"
    results_dir: str = "results"
    logs_dir: str = "logs"
    templates_dir: str = "templates"


@dataclass
class ProjectConfig:
    """项目配置主类"""
    repos: List[RepoConfig]
    symbols: List[SymbolConfig]
    thresholds: ThresholdConfig
    windows: WindowConfig
    paths: PathConfig
    sentiment_threshold: float = 0.3
    max_commits: Optional[int] = None
    cache_commits: bool = True
    generated_at: str = None

    def __post_init__(self):
        """初始化后处理"""
        if self.generated_at is None:
            self.generated_at = datetime.now().isoformat()


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG = {
        "repos": [
            {"owner": "tensorflow", "repo": "tensorflow", "days": 30}
        ],
        "symbols": [
            {"symbol": "AAPL", "initial_capital": 10000.0}
        ],
        "thresholds": {
            "sentiment_threshold": 0.3,
            "min_hold_hours": 24
        },
        "windows": {
            "window_hours": 24,
            "trend_window_hours": 48
        },
        "paths": {
            "data_dir": "data",
            "results_dir": "results",
            "logs_dir": "logs",
            "templates_dir": "templates"
        },
        "max_commits": None,
        "cache_commits": True
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path
        self.config = self._load_default_config()

        if config_path and os.path.exists(config_path):
            try:
                self.load_from_file(config_path)
            except Exception as e:
                print(f"Error loading config file: {e}")
                print("Using default configuration")

    def _load_default_config(self) -> Dict:
        """加载默认配置"""
        return self.DEFAULT_CONFIG.copy()

    def load_from_file(self, config_path: str) -> 'ConfigManager':
        """
        从文件加载配置

        Args:
            config_path: 配置文件路径（JSON 或 YAML）

        Returns:
            self
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            # 检测文件扩展名
            ext = os.path.splitext(config_path)[1].lower()

            if ext in ['.yml', '.yaml']:
                try:
                    import yaml
                    config = yaml.safe_load(f)
                except ImportError:
                    raise ImportError(
                        "PyYAML not installed. Install with: pip install pyyaml"
                    )
            else:
                # 默认为 JSON
                config = json.load(f)

        self.config.update(config)
        return self

    def load_from_dict(self, config_dict: Dict) -> 'ConfigManager':
        """
        从字典加载配置

        Args:
            config_dict: 配置字典

        Returns:
            self
        """
        self.config.update(config_dict)
        return self

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持嵌套 key）

        Args:
            key: 配置键（如 'thresholds.sentiment_threshold'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set_value(self, key: str, value: Any):
        """
        设置配置值（支持嵌套 key）

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_repos(self) -> List[RepoConfig]:
        """获取仓库配置列表"""
        repos = []
        for repo_data in self.config.get('repos', []):
            repos.append(RepoConfig(**repo_data))
        return repos

    def get_symbols(self) -> List[SymbolConfig]:
        """获取股票配置列表"""
        symbols = []
        for symbol_data in self.config.get('symbols', []):
            symbols.append(SymbolConfig(**symbol_data))
        return symbols

    def get_thresholds(self) -> ThresholdConfig:
        """获取阈值配置"""
        thresholds_data = self.config.get('thresholds', {})
        return ThresholdConfig(**thresholds_data)

    def get_windows(self) -> WindowConfig:
        """获取时间窗口配置"""
        windows_data = self.config.get('windows', {})
        return WindowConfig(**windows_data)

    def get_paths(self) -> PathConfig:
        """获取路径配置"""
        paths_data = self.config.get('paths', {})
        return PathConfig(**paths_data)

    def get_full_config(self) -> ProjectConfig:
        """获取完整的项目配置"""
        return ProjectConfig(
            repos=self.get_repos(),
            symbols=self.get_symbols(),
            thresholds=self.get_thresholds(),
            windows=self.get_windows(),
            paths=self.get_paths(),
            sentiment_threshold=self.get_value('sentiment_threshold', 0.3),
            max_commits=self.get_value('max_commits'),
            cache_commits=self.get_value('cache_commits', True),
            generated_at=datetime.now().isoformat()
        )

    def save_to_file(self, config_path: Optional[str] = None):
        """
        保存配置到文件

        Args:
            config_path: 保存路径（如果未提供，则使用初始化时的路径）
        """
        if config_path is None:
            config_path = self.config_path

        if config_path is None:
            raise ValueError("No config path specified")

        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return self.config.copy()


# 方便使用的函数
def load_config(config_path: str) -> ConfigManager:
    """
    从文件加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigManager 实例
    """
    return ConfigManager(config_path)


def create_default_config() -> ConfigManager:
    """
    创建默认配置

    Returns:
        ConfigManager 实例
    """
    return ConfigManager()


def create_config(
    repos: List[Dict],
    symbols: List[Dict],
    thresholds: Dict = None,
    windows: Dict = None,
    paths: Dict = None
) -> ConfigManager:
    """
    快速创建配置

    Args:
        repos: 仓库配置列表
        symbols: 股票配置列表
        thresholds: 阈值配置
        windows: 时间窗口配置
        paths: 路径配置

    Returns:
        ConfigManager 实例
    """
    config = ConfigManager()

    config.config['repos'] = repos
    config.config['symbols'] = symbols

    if thresholds:
        config.config['thresholds'] = thresholds
    if windows:
        config.config['windows'] = windows
    if paths:
        config.config['paths'] = paths

    return config
