"""
Logger Module

提供不同级别的日志记录功能，支持控制台输出和文件保存。
"""

import logging
import os
from datetime import datetime
from typing import Optional


class ProjectLogger:
    """项目日志记录器"""

    def __init__(
        self,
        name: str = "CommitSentimentTrader",
        log_dir: str = "logs",
        level: int = logging.INFO
    ):
        """
        初始化日志记录器

        Args:
            name: Logger 名称
            log_dir: 日志文件目录
            level: 日志级别 (logging.DEBUG, logging.INFO, etc.)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.log_dir = log_dir
        self.level = level

        # 避免重复添加 handler
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """设置日志处理器"""
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)

        # 日志格式
        log_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        console_handler.setFormatter(log_format)
        self.logger.addHandler(console_handler)

        # 文件处理器 - INFO 级别及以上
        info_file = os.path.join(self.log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
        info_handler = logging.FileHandler(info_file, encoding='utf-8')
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(log_format)
        self.logger.addHandler(info_handler)

        # 文件处理器 - ERROR 级别及以上
        error_file = os.path.join(self.log_dir, f"error_{datetime.now().strftime('%Y%m%d')}.log")
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(log_format)
        self.logger.addHandler(error_handler)

    def debug(self, message: str, **kwargs):
        """DEBUG 级别日志"""
        if kwargs:
            message = f"{message} | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.debug(message)

    def info(self, message: str, **kwargs):
        """INFO 级别日志"""
        if kwargs:
            message = f"{message} | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(message)

    def warning(self, message: str, **kwargs):
        """WARNING 级别日志"""
        if kwargs:
            message = f"{message} | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.warning(message)

    def error(self, message: str, **kwargs):
        """ERROR 级别日志"""
        if kwargs:
            message = f"{message} | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.error(message)

    def critical(self, message: str, **kwargs):
        """CRITICAL 级别日志"""
        if kwargs:
            message = f"{message} | " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.critical(message)

    def log_exception(self, exception: Exception, context: dict = None):
        """记录异常及其上下文"""
        self.logger.exception(
            f"Exception occurred: {str(exception)}",
            extra={'context': context}
        )


def get_logger(name: str = "CommitSentimentTrader") -> ProjectLogger:
    """
    获取日志记录器实例

    Args:
        name: Logger 名称

    Returns:
        ProjectLogger 实例
    """
    return ProjectLogger(name=name)


# 方便使用的函数
def setup_logger(
    name: str = "CommitSentimentTrader",
    log_dir: str = "logs",
    level: int = logging.INFO
) -> ProjectLogger:
    """
    设置并返回日志记录器

    Args:
        name: Logger 名称
        log_dir: 日志文件目录
        level: 日志级别

    Returns:
        ProjectLogger 实例
    """
    logger = ProjectLogger(name=name, log_dir=log_dir, level=level)
    return logger


# 模块级别的默认 logger
_default_logger: Optional[ProjectLogger] = None


def log_debug(message: str, **kwargs):
    """模块级别 DEBUG 日志"""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger()
    _default_logger.debug(message, **kwargs)


def log_info(message: str, **kwargs):
    """模块级别 INFO 日志"""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger()
    _default_logger.info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """模块级别 WARNING 日志"""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger()
    _default_logger.warning(message, **kwargs)


def log_error(message: str, **kwargs):
    """模块级别 ERROR 日志"""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger()
    _default_logger.error(message, **kwargs)


def log_critical(message: str, **kwargs):
    """模块级别 CRITICAL 日志"""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger()
    _default_logger.critical(message, **kwargs)
