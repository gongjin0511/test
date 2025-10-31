"""
OKX Exchange Client using CCXT
"""

import ccxt
import time
from typing import List, Optional, Dict
from .types import (
    MarketSnapshot, AccountState, AccountPosition, OrderParams,
    OrderResult, OHLCV, TechnicalIndicators, PositionSide,
    OrderSide, OrderType, ExchangeError
)
from .indicators import calculate_all_indicators


class OKXClient:
    """OKX exchange client wrapper"""

    def __init__(self, api_key: str, secret_key: str, passphrase: str, testnet: bool = True):
        self.exchange = ccxt.okx({
            'apiKey': api_key,
            'secret': secret_key,
            'password': passphrase,
            'enableRateLimit': True,
        })

        if testnet:
            self.exchange.set_sandbox_mode(True)

    async def test_connection(self) -> bool:
        """Test connection to OKX"""
        try:
            await self.exchange.fetch_status()
            return True
        except Exception as e:
            raise ExchangeError(f"Failed to connect to OKX: {str(e)}")

    async def get_market_data(self, symbol: str) -> MarketSnapshot:
        """Get market data for a symbol"""
        try:
            # Fetch ticker
            ticker = await self.exchange.fetch_ticker(symbol)

            # Fetch OHLCV data (1m candles, 100 bars)
            candles_data = await self.exchange.fetch_ohlcv(symbol, '1m', limit=100)
            candles = [
                OHLCV(
                    timestamp=int(c[0]),
                    open=float(c[1]),
                    high=float(c[2]),
                    low=float(c[3]),
                    close=float(c[4]),
                    volume=float(c[5])
                )
                for c in candles_data
            ]

            # Calculate technical indicators
            close_prices = [c.close for c in candles]
            indicators = calculate_all_indicators(close_prices, candles)

            return MarketSnapshot(
                symbol=symbol,
                price=float(ticker['last']),
                price_change_24h=float(ticker['percentage'] or 0),
                volume_24h=float(ticker['quoteVolume'] or 0),
                high_24h=float(ticker['high']),
                low_24h=float(ticker['low']),
                funding_rate=float(ticker.get('info', {}).get('fundingRate', 0)),
                open_interest=float(ticker.get('info', {}).get('openInterest', 0)),
                indicators=indicators,
                recent_candles=candles[-20:]  # Last 20 candles
            )

        except Exception as e:
            raise ExchangeError(f"Failed to get market data for {symbol}: {str(e)}")

    async def get_account_state(self) -> AccountState:
        """Get account state"""
        try:
            balance = await self.exchange.fetch_balance()
            positions = await self.get_positions()

            total_equity = float(balance.get('total', {}).get('USDT', 0))
            unrealized_pnl = sum(p.unrealized_pnl for p in positions)
            used_margin = sum(p.size * p.entry_price / p.leverage for p in positions)

            return AccountState(
                total_equity=total_equity + unrealized_pnl,
                available_balance=total_equity - used_margin,
                used_margin=used_margin,
                unrealized_pnl=unrealized_pnl,
                positions=positions,
                open_orders_count=len(await self.exchange.fetch_open_orders())
            )

        except Exception as e:
            raise ExchangeError(f"Failed to get account state: {str(e)}")

    async def get_positions(self) -> List[AccountPosition]:
        """Get current positions"""
        try:
            positions_data = await self.exchange.fetch_positions()

            positions = []
            for pos in positions_data:
                if float(pos.get('contracts', 0)) > 0:
                    positions.append(AccountPosition(
                        symbol=pos['symbol'],
                        side=PositionSide.LONG if pos['side'] == 'long' else PositionSide.SHORT,
                        size=float(pos['contracts']),
                        entry_price=float(pos['entryPrice']),
                        current_price=float(pos['markPrice']),
                        leverage=int(pos['leverage']),
                        unrealized_pnl=float(pos['unrealizedPnl']),
                        unrealized_pnl_percent=float(pos['percentage']),
                        liquidation_price=float(pos.get('liquidationPrice', 0)),
                        timestamp=int(time.time() * 1000)
                    ))

            return positions

        except Exception as e:
            raise ExchangeError(f"Failed to get positions: {str(e)}")

    async def place_order(self, params: OrderParams) -> OrderResult:
        """Place an order"""
        try:
            # Set leverage if specified
            if params.leverage:
                await self.exchange.set_leverage(params.leverage, params.symbol)

            # Place order
            order = await self.exchange.create_order(
                symbol=params.symbol,
                type=params.type.value,
                side=params.side.value,
                amount=params.quantity,
                price=params.price
            )

            return OrderResult(
                order_id=order['id'],
                symbol=params.symbol,
                status=order['status'],
                filled_quantity=float(order['filled']),
                average_price=float(order['average'] or params.price or 0),
                timestamp=int(order['timestamp']),
                fee=float(order.get('fee', {}).get('cost', 0))
            )

        except Exception as e:
            raise ExchangeError(f"Failed to place order: {str(e)}")

    async def close_position(self, symbol: str) -> OrderResult:
        """Close a position"""
        try:
            # Get current position
            positions = await self.get_positions()
            position = next((p for p in positions if p.symbol == symbol), None)

            if not position:
                raise ExchangeError(f"No position found for {symbol}")

            # Place closing order
            side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY

            return await self.place_order(OrderParams(
                symbol=symbol,
                side=side,
                type=OrderType.MARKET,
                quantity=position.size
            ))

        except Exception as e:
            raise ExchangeError(f"Failed to close position for {symbol}: {str(e)}")


def create_okx_client(api_key: str, secret_key: str, passphrase: str, testnet: bool = True) -> OKXClient:
    """Create OKX client instance"""
    return OKXClient(api_key, secret_key, passphrase, testnet)
