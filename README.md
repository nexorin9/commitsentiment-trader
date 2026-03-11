# CommitSentiment Trader

将 GitHub commit 情绪分析结果映射为量化交易信号，探索软件开发活动与金融市场之间的意外关联。

## 项目介绍

这是一个实验性项目，通过分析开源项目的 GitHub commit 历史，构建情感时间序列，并将其转换为量化交易信号。项目旨在探索：

- 开发者情绪是否与代码质量/提交频率相关
- 情感趋势是否能预测股价波动
- 软件开发活动与金融市场之间的潜在关联

## 安装

```bash
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 到 `.env` 并填写你的 API 密钥：

```
GITHUB_TOKEN=your_github_token_here
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
```

## 使用方法

运行完整分析：

```bash
python examples/run_analysis.py --repo tensorflow/tensorflow --days 30 --symbol AAPL
```

命令行参数：
- `--repo`: GitHub 仓库（格式：owner/repo）
- `--days`: 分析天数范围
- `--symbol`: 股票代码

## 项目结构

```
commit-sentiment-trader/
├── src/          # 源代码模块
│   ├── github_fetcher.py      # GitHub API 获取 commit
│   ├── sentiment_analyzer.py  # 情感分析
│   ├── time_series.py         # 时间序列引擎
│   ├── signal_generator.py    # 交易信号生成
│   ├── alpaca_connector.py    # Alpaca API 连接
│   └── backtester.py          # 回测引擎
├── data/         # 数据文件（缓存、中间结果）
├── docs/         # 文档
├── examples/     # 示例脚本
├── results/      # 结果输出
└── tests/        # 单元测试
```

## 已知限制 (Known Limitations)

本项目是一个实验性研究项目，存在以下限制：

- **数据延迟**：GitHub API 和股票数据可能存在延迟
- **样本偏差**：只分析选定的 GitHub 仓库，不代表整体趋势
- **情感分析准确性**：基于 VADER 模型，对技术术语和代码相关表达的准确性有限
- **回测偏差**：历史回测结果不保证_future_表现
- **API 限制**：GitHub API 有速率限制，未认证用户每小时仅 60 次请求
- ** Trading 风险**：本项目不用于实际交易，仅用于研究目的

## 许可证

MIT License

---

## 支持作者

如果您觉得这个项目对您有帮助，欢迎打赏支持！

![Buy Me a Coffee](buymeacoffee.png)

**Buy me a coffee (crypto)**

| 币种 | 地址 |
|------|------|
| BTC | `bc1qc0f5tv577z7yt59tw8sqaq3tey98xehy32frzd` |
| ETH / USDT | `0x3b7b6c47491e4778157f0756102f134d05070704` |
| SOL | `6Xuk373zc6x6XWcAAuqvbWW92zabJdCmN3CSwpsVM6sd` |
