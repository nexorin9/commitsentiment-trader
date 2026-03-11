# 分析报告模板

**项目**: CommitSentiment Trader
**生成时间**: 2026-03-11 01:01:19
**报告版本**: 1.0

---

## 概览 (Overview)

本报告展示 GitHub commit 情感分析结果及基于情感的交易信号生成。

### 分析参数

| 参数 | 值 |
|------|-----|
| 仓库 (Repository) | test/repo |
| 分析日期范围 | 2026-01-01 to 2026-03-10 |
| 分析时间点 | 30 |
| 股票代码 (Symbol) | TEST |
| Sentiment 阈值 (Threshold) | 0.3 |

---

## 情感分析 (Sentiment Analysis)

### 基本统计

| 指标 | 数值 |
|------|------|
| 总 commit 数 | 150 |
| 平均情感分数 | 0.2500 |
| 正向比例 | 45.00% |
| 中性比例 | 35.00% |
| 负向比例 | 20.00% |

### 情感趋势

平均情感分数: **0.2500**

- **积极** (> 0.3): 68 个 commit (45.00%)
- **中性** (-0.3 to 0.3): 52 个 commit (35.00%)
- **消极** (< -0.3): 30 个 commit (20.00%)

### 示例 Commits

#### 积极情感示例
1. **Message**: "Updated README with new features"
   - 情感分数: 0.8500

2. **Message**: "Fixed critical bug in login"
   - 情感分数: 0.7200

#### 中性情感示例
1. **Message**: "Minor code cleanup"
   - 情感分数: 0.1000

#### 消极情感示例
1. **Message**: "Reverted unstable commit"
   - 情感分数: -0.6800

---

## 交易信号 (Trading Signals)

### 信号统计

| 信号类型 | 数量 |
|----------|------|
| 买入 (BUY) | 12 |
| 卖出 (SELL) | 8 |
| 持有 (HOLD) | 5 |
| **总计** | 25 |

### 信号时间线

- **首个信号**: 2026-01-01
- **最后一个信号**: 2026-03-10
- **信号密度**: 2.5 天/信号

### 信号详情

```
N/A
```

---

## 回测结果 (Backtest Results)

### 关键指标

| 指标 | 数值 |
|------|------|
| 初始资金 | $10,000.00 |
| 最终投资组合价值 | $11,000.00 |
| 总收益率 | 10.50% |
| 市场基准收益率 | 8.20% |
| **超额收益** | 2.30% |

### 风险调整后收益

| 指标 | 数值 |
|------|------|
| 夏普比率 (Sharpe Ratio) | 1.2500 |
| 最大回撤 (Max Drawdown) | 5.30% |
| 胜率 (Win Rate) | 60.00% |
| 盈亏比 (Profit Factor) | 1.5000 |
| 交易次数 | 25 |

### 投资组合价值走势

```
[图表: 投资组合价值随时间变化]
```

---

## 附录 (Appendix)

### 技术细节

- **Sentiment 分析器**: VADER (Valence Aware Dictionary for sEntiment Reasoning)
- **时间窗口**: 24 小时滚动窗口
- **证券数据源**: Alpaca API
- **报告生成工具**: CommitSentiment Trader v1.0

### 数据来源

- GitHub API: https://api.github.com/repos/test/repo/commits
- Alpaca API: https://api.alpaca.markets

### 注意事项

1. 本报告基于历史数据回测，不保证未来表现
2. 实际交易涉及滑点、执行延迟、市场冲击等额外因素
3. Sentiment 分析基于 commit message 文本，可能不完全反映实际开发状态
4. 回测使用模拟数据，实际回测需配置真实 Alpaca API 凭证

---

### 生成信息

- **报告生成时间**: 2026-03-11 01:01:19
- **Generator 版本**: CommitSentiment Trader v1.0
- **配置文件**: config.json

---

*本报告由 CommitSentiment Trader 自动生成*
