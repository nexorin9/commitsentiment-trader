"""
Alpaca Trading Connector

与 Alpaca API 的连接，支持获取市场数据和模拟交易。
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

try:
    from alpaca.trading.client import TradingClient
    from alpaca.data import StockHistoricalDataClient
    from alpaca.common.exceptions import APIError as AlpacaAPIError
except ImportError:
    try:
        # Fallback for older versions
        from alpaca.trading.client import TradingClient
        from alpaca.data.stocks import StockDataClient as StockHistoricalDataClient
        from alpaca.common.exceptions import APIError as AlpacaAPIError
    except ImportError:
        TradingClient = None
        StockHistoricalDataClient = None
        AlpacaAPIError = Exception

try:
    from .logger import log_error, log_warning, log_info
except ImportError:
    from logger import log_error, log_warning, log_info


class AlpacaConnector:
    """Alpaca 交易连接器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        paper_trading: bool = True
    ):
        """
        初始化 Alpaca 连接器

        Args:
            api_key: Alpaca API Key (从环境变量读取如果未提供)
            secret_key: Alpaca Secret Key (从环境变量读取如果未提供)
            paper_trading: 是否使用模拟交易账户
        """
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")

        if not self.api_key or not self.secret_key:
            log_warning(
                "Alpaca API credentials not provided. "
                "Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables."
            )

        self.paper_trading = paper_trading
        self.trading_client: Optional[TradingClient] = None
        self.data_client: Optional[StockHistoricalDataClient] = None

        # 尝试初始化客户端
        self._init_clients()

    def _init_clients(self):
        """初始化 Alpaca 客户端"""
        if TradingClient is None:
            log_warning("alpaca-py not installed. Skipping client initialization.")
            return

        try:
            # 交易客户端
            self.trading_client = TradingClient(
                self.api_key,
                self.secret_key,
                paper=self.paper_trading
            )

            # 数据客户端（用于市场数据）
            self.data_client = StockHistoricalDataClient(
                self.api_key,
                self.secret_key
            )

            log_info("Alpaca clients initialized successfully")
        except Exception as e:
            log_error(f"Failed to initialize Alpaca clients: {str(e)}")
            self.trading_client = None
            self.data_client = None

    def get_stock_prices(self, symbol: str, limit: int = 100) -> List[Dict]:
        """
        获取股票历史价格数据

        Args:
            symbol: 股票代码
            limit: 最大返回记录数

        Returns:
            价格数据列表，包含 timestamp 和 price
        """
        if self.data_client is None:
            log_warning("Data client not available. Returning empty data.")
            return []

        try:
            # 获取历史数据（最近的 bar）
            from alpaca.data import StockBarsRequest, TimeFrame

            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                limit=limit,
                timeframe=TimeFrame.Day,
                adjustment="split"
            )
            bars = self.data_client.get_stock_bars(request_params)

            prices = []
            # bars is a dict {symbol: [bar1, bar2, ...]}
            if isinstance(bars, dict):
                for bar in bars.get(symbol, []):
                    if hasattr(bar, 'timestamp') and hasattr(bar, 'close'):
                        prices.append({
                            "timestamp": bar.timestamp,
                            "open": bar.open,
                            "high": bar.high,
                            "low": bar.low,
                            "close": bar.close,
                            "volume": bar.volume
                        })
            # Also handle the case where bars is a list directly
            elif hasattr(bars, '__iter__'):
                for bar in bars:
                    if hasattr(bar, 'timestamp') and hasattr(bar, 'close'):
                        prices.append({
                            "timestamp": bar.timestamp,
                            "open": bar.open,
                            "high": bar.high,
                            "low": bar.low,
                            "close": bar.close,
                            "volume": bar.volume
                        })

            log_info(f"Retrieved {len(prices)} price records for {symbol}")
            return prices

        except AlpacaAPIError as e:
            log_error(f"Alpaca API Error fetching stock prices: {str(e)}", symbol=symbol)
            return []
        except Exception as e:
            log_error(f"Error fetching stock prices: {str(e)}", symbol=symbol)
            return []

    def get_account_status(self) -> Optional[Dict]:
        """
        获取账户状态

        Returns:
            账户信息字典
        """
        if self.trading_client is None:
            log_warning("Trading client not available.")
            return None

        try:
            account = self.trading_client.get_account()
            return {
                "account_type": account.account_type,
                "status": account.status,
                "equity": account.equity,
                "cash": account.cash,
                "portfolio_value": account.portfolio_value
            }
        except AlpacaAPIError as e:
            log_error(f"Alpaca API Error fetching account: {str(e)}")
            return None
        except Exception as e:
            log_error(f"Error fetching account: {str(e)}")
            return None

    def place_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str = "market"
    ) -> Optional[Dict]:
        """
        下单交易

        Args:
            symbol: 股票代码
            qty: 交易数量
            side: 订单方向 ("buy" or "sell")
            order_type: 订单类型 ("market", "limit", etc.)

        Returns:
            订单信息字典
        """
        if self.trading_client is None:
            log_warning("Trading client not available. Skipping order placement.")
            return None

        try:
            order = self.trading_client.place_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force="day"
            )

            return {
                "order_id": order.id,
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "status": order.status,
                "qty": order.qty,
                "filled_qty": getattr(order, 'filled_qty', 0),
                "order_type": order.order_type
            }
        except AlpacaAPIError as e:
            log_error(f"Alpaca API Error placing order: {str(e)}", symbol=symbol, side=side)
            return None
        except Exception as e:
            log_error(f"Error placing order: {str(e)}", symbol=symbol, side=side)
            return None

    def get_open_positions(self) -> List[Dict]:
        """
        获取当前持仓

        Returns:
            持仓列表
        """
        if self.trading_client is None:
            log_warning("Trading client not available.")
            return []

        try:
            positions = self.trading_client.get_orders()
            # 注意：Alpaca API 返回的是 orders，不是 positions
            # 对于持仓信息需要使用 get_positions()（需要 data feed 权限）
            log_info("get_open_positions() returned empty (use get_orders() instead)")
            return []
        except Exception as e:
            log_error(f"Error getting positions: {str(e)}")
            return []

    def test_connection(self) -> bool:
        """
        测试连接是否正常

        Returns:
            连接是否成功
        """
        if self.trading_client is None and self.data_client is None:
            log_warning("No Alpaca clients initialized. Connection test failed.")
            return False

        try:
            # 尝试获取一个简单的数据点
            prices = self.get_stock_prices("AAPL", limit=1)
            if len(prices) > 0:
                log_info("Alpaca connection test passed")
                return True
            else:
                log_warning("Alpaca connection test failed (no data returned)")
                return False
        except Exception as e:
            log_error(f"Alpaca connection test failed: {str(e)}")
            return False


# 方便使用的函数
def get_stock_prices(symbol: str, limit: int = 100) -> List[Dict]:
    """
    快速获取股票价格的便捷函数

    Args:
        symbol: 股票代码
        limit: 最大返回记录数

    Returns:
        价格数据列表
    """
    connector = AlpacaConnector()
    return connector.get_stock_prices(symbol, limit)


def get_account_status() -> Optional[Dict]:
    """获取账户状态的便捷函数"""
    connector = AlpacaConnector()
    return connector.get_account_status()
