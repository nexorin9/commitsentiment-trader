# 分析报告模板

**项目**: CommitSentiment Trader
**生成时间**: {generated_at}
**报告版本**: 1.0

---

## 概览 (Overview)

本报告展示 GitHub commit 情感分析结果及基于情感的交易信号生成。

### 分析参数

| 参数 | 值 |
|------|-----|
| 仓库 (Repository) | {repo} |
| 分析日期范围 | {date_range} |
| 分析时间点 | {num_time_points} |
| 股票代码 (Symbol) | {symbol} |
| Sentiment 阈值 (Threshold) | {threshold} |

---

## 情感分析 (Sentiment Analysis)

### 基本统计

| 指标 | 数值 |
|------|------|
| 总 commit 数 | {commits_count} |
| 平均情感分数 | {avg_sentiment:.4f} |
| 正向比例 | {positive_ratio:.2%} |
| 中性比例 | {neutral_ratio:.2%} |
| 负向比例 | {negative_ratio:.2%} |

### 情感趋势

平均情感分数: **{avg_sentiment:.4f}**

- **积极** (> 0.3): {positive_count} 个 commit ({positive_ratio:.2%})
- **中性** (-0.3 to 0.3): {neutral_count} 个 commit ({neutral_ratio:.2%})
- **消极** (< -0.3): {negative_count} 个 commit ({negative_ratio:.2%})

### 示例 Commits

#### 积极情感示例
1. **Message**: "{positive_sample_1}"
   - 情感分数: {positive_score_1:.4f}

2. **Message**: "{positive_sample_2}"
   - 情感分数: {positive_score_2:.4f}

#### 中性情感示例
1. **Message**: "{neutral_sample_1}"
   - 情感分数: {neutral_score_1:.4f}

#### 消极情感示例
1. **Message**: "{negative_sample_1}"
   - 情感分数: {negative_score_1:.4f}

---

## 交易信号 (Trading Signals)

### 信号统计

| 信号类型 | 数量 |
|----------|------|
| 买入 (BUY) | {buy_signals} |
| 卖出 (SELL) | {sell_signals} |
| 持有 (HOLD) | {hold_signals} |
| **总计** | {total_signals} |

### 信号时间线

- **首个信号**: {first_signal_date}
- **最后一个信号**: {last_signal_date}
- **信号密度**: {signal_density} 天/信号

### 信号详情

```
{signals_table}
```

---

## 回测结果 (Backtest Results)

### 关键指标

| 指标 | 数值 |
|------|------|
| 初始资金 | ${initial_capital:,.2f} |
| 最终投资组合价值 | ${final_value:,.2f} |
| 总收益率 | {total_return:.2f}% |
| 市场基准收益率 | {market_return:.2f}% |
| **超额收益** | {alpha:.2f}% |

### 风险调整后收益

| 指标 | 数值 |
|------|------|
| 夏普比率 (Sharpe Ratio) | {sharpe_ratio:.4f} |
| 最大回撤 (Max Drawdown) | {max_drawdown:.2f}% |
| 胜率 (Win Rate) | {win_rate:.2f}% |
| 盈亏比 (Profit Factor) | {profit_factor:.4f} |
| 交易次数 | {trades_count} |

### 投资组合价值走势

```
[图表: 投资组合价值随时间变化]
```

---

## 附录 (Appendix)

### 技术细节

- **Sentiment 分析器**: VADER (Valence Aware Dictionary for sEntiment Reasoning)
- **时间窗口**: {window_hours} 小时滚动窗口
- **证券数据源**: Alpaca API
- **报告生成工具**: CommitSentiment Trader v1.0

### 数据来源

- GitHub API: https://api.github.com/repos/{repo}/commits
- Alpaca API: https://api.alpaca.markets

### 注意事项

1. 本报告基于历史数据回测，不保证未来表现
2. 实际交易涉及滑点、执行延迟、市场冲击等额外因素
3. Sentiment 分析基于 commit message 文本，可能不完全反映实际开发状态
4. 回测使用模拟数据，实际回测需配置真实 Alpaca API 凭证

---

### 生成信息

- **报告生成时间**: {generated_at}
- **Generator 版本**: CommitSentiment Trader v1.0
- **配置文件**: {config_file}

---

*本报告由 CommitSentiment Trader 自动生成*
