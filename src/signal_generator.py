"""
Trading Signal Generator

基于 sentiment 的交易信号生成逻辑，定义买卖规则。
"""

import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class TradingSignal(Enum):
    """交易信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalGenerator:
    """交易信号生成器"""

    def __init__(
        self,
        threshold: float = 0.3,
        min_hold_hours: int = 4
    ):
        """
        初始化信号生成器

        Args:
            threshold: 情感阈值，超过此值才触发信号
            min_hold_hours: 最小持有时间（小时），避免频繁切换
        """
        self.threshold = threshold
        self.min_hold_hours = min_hold_hours
        self.last_signal: Optional[TradingSignal] = None
        self.last_signal_time: Optional[datetime] = None

    def generate_signals(
        self,
        sentiment_data: Dict,
        threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        基于情感数据生成交易信号

        Args:
            sentiment_data: 包含时间序列情感数据的字典
                格式：{"timestamps": [...], "sentiments": [...]}
            threshold: 情感阈值（可覆盖默认值）

        Returns:
            信号列表，每个信号包含 timestamp、signal_type、reason
        """
        if not sentiment_data or "sentiments" not in sentiment_data:
            return []

        thresholds = threshold or self.threshold
        signals = []

        sentiments = sentiment_data["sentiments"]
        timestamps = sentiment_data.get("timestamps", [])

        for i, sent in enumerate(sentiments):
            signal_type, reason = self._determine_signal(sent, thresholds)

            if signal_type != TradingSignal.HOLD:
                # 检查是否满足最小持有时间
                ts = timestamps[i] if timestamps else datetime.now()
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))

                if self._can_switch_signal(signal_type, ts):
                    signals.append({
                        "timestamp": str(timestamps[i]) if timestamps else f"index_{i}",
                        "signal": signal_type.value,
                        "sentiment_score": sent,
                        "reason": reason
                    })
                    self.last_signal = signal_type
                    self.last_signal_time = ts

        return signals

    def _determine_signal(
        self,
        sentiment: float,
        threshold: float
    ) -> tuple:
        """
        确定单个时间点的交易信号

        Args:
            sentiment: 情感分数 (-1 到 +1)
            threshold: 阈值

        Returns:
            (signal_type, reason) 元组
        """
        if sentiment > threshold:
            return TradingSignal.BUY, f"High positive sentiment ({sentiment:.3f})"
        elif sentiment < -threshold:
            return TradingSignal.SELL, f"High negative sentiment ({sentiment:.3f})"
        else:
            # 如果当前没有持仓，保持 HOLD
            # 如果已有持仓，根据方向决定是否保持
            if self.last_signal == TradingSignal.BUY and sentiment > 0:
                return TradingSignal.HOLD, "Maintaining BUY position"
            elif self.last_signal == TradingSignal.SELL and sentiment < 0:
                return TradingSignal.HOLD, "Maintaining SELL position"
            else:
                return TradingSignal.HOLD, "Neutral sentiment"

    def _can_switch_signal(
        self,
        new_signal: TradingSignal,
        timestamp: datetime
    ) -> bool:
        """
        检查是否可以切换到新信号

        Args:
            new_signal: 新的信号类型
            timestamp: 当前时间戳

        Returns:
            是否允许切换
        """
        if self.last_signal is None:
            return True

        if self.last_signal == new_signal:
            return False

        if self.last_signal_time is None:
            return True

        time_diff = (timestamp - self.last_signal_time).total_seconds() / 3600
        return time_diff >= self.min_hold_hours

    def save_signals(self, signals: List[Dict], output_path: str):
        """
        保存信号到 JSON 文件

        Args:
            signals: 信号列表
            output_path: 输出文件路径
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        data = {
            "generated_at": datetime.now().isoformat(),
            "signals": signals,
            "total_signals": len(signals),
            "buy_signals": sum(1 for s in signals if s["signal"] == TradingSignal.BUY.value),
            "sell_signals": sum(1 for s in signals if s["signal"] == TradingSignal.SELL.value)
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"Saved {data['total_signals']} signals to {output_path}")


# 方便使用的函数
def generate_signals(
    sentiment_data: Dict,
    threshold: float = 0.3
) -> List[Dict]:
    """
    快速生成交易信号的便捷函数

    Args:
        sentiment_data: 情感数据字典
        threshold: 情感阈值

    Returns:
        信号列表
    """
    generator = SignalGenerator(threshold=threshold)
    return generator.generate_signals(sentiment_data)


def save_signals(signals: List[Dict], output_path: str):
    """
    保存信号到文件的便捷函数

    Args:
        signals: 信号列表
        output_path: 输出路径
    """
    generator = SignalGenerator()
    generator.save_signals(signals, output_path)
