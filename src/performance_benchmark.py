"""
Performance Benchmark Module

用于测量和对比优化前后的性能表现。
"""

import time
from datetime import datetime
from typing import Dict, List, Tuple


class BenchmarkResult:
    """性能测试结果"""

    def __init__(self, name: str, duration: float, items_processed: int):
        self.name = name
        self.duration = duration
        self.items_processed = items_processed

    @property
    def items_per_second(self) -> float:
        return self.items_processed / self.duration if self.duration > 0 else 0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "duration_seconds": round(self.duration, 3),
            "items_processed": self.items_processed,
            "items_per_second": round(self.items_per_second, 2),
            "timestamp": datetime.now().isoformat()
        }

    def __str__(self) -> str:
        return (
            f"{self.name}: {self.duration:.3f}s "
            f"({self.items_processed} items, {self.items_per_second:.2f} items/s)"
        )


class PerformanceBenchmark:
    """性能基准测试工具"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self._start_time = None

    def start(self):
        """开始计时"""
        self._start_time = time.perf_counter()

    def stop(self, name: str, items_count: int) -> BenchmarkResult:
        """停止计时并记录结果"""
        if self._start_time is None:
            raise ValueError("Benchmark not started. Call start() first.")

        duration = time.perf_counter() - self._start_time
        result = BenchmarkResult(name, duration, items_count)
        self.results.append(result)
        self._start_time = None
        return result

    def run_comparison(
        self,
        name_a: str,
        func_a,
        name_b: str,
        func_b,
        test_data
    ) -> Tuple[BenchmarkResult, BenchmarkResult]:
        """对比两个函数的性能"""
        # Run A
        self.start()
        result_a_data = func_a(test_data)
        result_a = self.stop(name_a, len(test_data) if hasattr(test_data, '__len__') else 100)

        # Run B
        self.start()
        result_b_data = func_b(test_data)
        result_b = self.stop(name_b, len(test_data) if hasattr(test_data, '__len__') else 100)

        return result_a, result_b

    def print_report(self):
        """打印性能报告"""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARK REPORT")
        print("=" * 60)

        if not self.results:
            print("No results to report.")
            return

        for i, result in enumerate(self.results, 1):
            print(f"\n{i}. {result}")
            if result.duration >= 1.0:
                print(f"   ⚠️  Slow operation (>1s)")

        # Find best/worst
        if len(self.results) >= 2:
            fastest = min(self.results, key=lambda r: r.duration)
            slowest = max(self.results, key=lambda r: r.duration)
            print(f"\nFastest: {fastest.name} ({fastest.duration:.3f}s)")
            print(f"Slowest: {slowest.name} ({slowest.duration:.3f}s)")

        print("\n" + "=" * 60)


# Global benchmark instance
default_benchmark = PerformanceBenchmark()


def benchmark_performance(test_name: str, items_count: int = 100):
    """
    性能装饰器，用于测量函数执行时间

    Args:
        test_name: 测试名称
        items_count: 处理的项目数量

    Usage:
        @benchmark_performance("test_name", 100)
        def test_func(data):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start

            benchmark = PerformanceBenchmark()
            benchmark.results.append(BenchmarkResult(test_name, duration, items_count))
            print(f"{test_name}: {duration:.3f}s")

            return result
        return wrapper
    return decorator
