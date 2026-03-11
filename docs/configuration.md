# 配置说明

本项目需要配置以下环境变量：

## GitHub Token

用于访问 GitHub API，获取 commit 历史。

### 获取方式

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置权限：
   - `repo` - Read access to code
   - `public_repo` - Read public repositories
4. 生成并复制 token

### 环境变量

```
GITHUB_TOKEN=your_github_token_here
```

## Alpaca API Keys

用于访问 Alpaca 交易 API，获取市场数据和进行交易。

### 获取方式

1. 访问 https://app.alpaca.markets/
2. 注册账户并完成验证
3. 访问 https://app.alpaca.markets/paper/dashboard/overview
4. 点击 "API Keys" → "Generate New Key"
5. 复制 API Key 和 Secret Key

### 环境变量

```
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
```

## 完整配置示例

创建 `.env` 文件：

```
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ALPACA_API_KEY=AKxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ALPACA_SECRET_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 可选配置

### 分析参数

可以在 `src/config.py` 或命令行中配置：

- `--days`: 分析天数范围（默认：30）
- `--repo`: GitHub 仓库（格式：owner/repo）
- `--symbol`: 股票代码（默认：AAPL）
- `--threshold`: 信号阈值（默认：0.3）

### 模型参数

- `--window-hours`: 时间序列滚动窗口（小时，默认：24）
- `--min-hold-time`: 最小持仓时间（默认：1）
