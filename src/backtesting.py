"""
LLM-Based Backtesting Engine
Uses AI to analyze historical data and generate insights
"""

import asyncio
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from .types import (
    TradingDecision, MarketSnapshot, AccountState, MarketState,
    TradeRecord, PerformanceMetrics, TradingAction, ExitPlan
)
from .ai_provider_enhanced import EnhancedAnthropicProvider
from .risk_manager import RiskManager
from .database import TradingDatabase
from .config import SystemConfig
import logging


class BacktestResult:
    """Result of a backtest run"""

    def __init__(
        self,
        period_start: int,
        period_end: int,
        trades: List[TradeRecord],
        performance: PerformanceMetrics,
        ai_insights: str,
        strategy_name: str
    ):
        self.period_start = period_start
        self.period_end = period_end
        self.trades = trades
        self.performance = performance
        self.ai_insights = ai_insights
        self.strategy_name = strategy_name


class LLMBacktester:
    """
    LLM-powered backtesting engine.

    Unlike traditional backtesting, this uses the actual AI to:
    1. Make trading decisions on historical data
    2. Analyze what worked and what didn't
    3. Generate insights about market conditions
    4. Suggest strategy improvements
    """

    def __init__(
        self,
        config: SystemConfig,
        ai_provider: EnhancedAnthropicProvider,
        risk_manager: RiskManager,
        database: TradingDatabase,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.ai_provider = ai_provider
        self.risk_manager = risk_manager
        self.database = database
        self.logger = logger or logging.getLogger(__name__)

    async def run_backtest(
        self,
        historical_data: Dict[str, pd.DataFrame],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        strategy_name: str = "AI Trading Strategy"
    ) -> BacktestResult:
        """
        Run backtest on historical data using AI decisions.

        Args:
            historical_data: Dict of {symbol: DataFrame} with OHLCV data
            start_date: Start date for backtest
            end_date: End date for backtest
            initial_capital: Starting capital
            strategy_name: Name of the strategy being tested

        Returns:
            BacktestResult with trades, performance, and AI insights
        """

        self.logger.info("=" * 80)
        self.logger.info(f"🔬 Starting LLM-Based Backtest: {strategy_name}")
        self.logger.info("=" * 80)
        self.logger.info(f"Period: {start_date} to {end_date}")
        self.logger.info(f"Initial Capital: ${initial_capital:,.2f}")
        self.logger.info(f"Symbols: {list(historical_data.keys())}")
        self.logger.info("=" * 80)

        # Initialize backtest state
        current_capital = initial_capital
        total_equity = initial_capital
        trades: List[TradeRecord] = []
        open_positions: Dict[str, TradeRecord] = {}

        # Convert to timestamps
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        # Get all timestamps (using first symbol's data as reference)
        first_symbol = list(historical_data.keys())[0]
        df = historical_data[first_symbol]

        # Filter to backtest period
        df_period = df[(df.index >= start_date) & (df.index <= end_date)]
        timestamps = df_period.index

        self.logger.info(f"Total timepoints to simulate: {len(timestamps)}")

        # Simulate trading through time
        for i, timestamp in enumerate(timestamps):
            if i % 100 == 0:
                self.logger.info(f"Progress: {i}/{len(timestamps)} ({i/len(timestamps)*100:.1f}%)")

            # Build market state at this timestamp
            market_state = self._build_market_state(
                timestamp=timestamp,
                historical_data=historical_data,
                current_capital=current_capital,
                total_equity=total_equity,
                open_positions=open_positions
            )

            # Check exit conditions for open positions
            closed_trades = self._check_exits(
                timestamp=timestamp,
                historical_data=historical_data,
                open_positions=open_positions
            )

            for trade in closed_trades:
                trades.append(trade)
                current_capital += trade.pnl or 0
                self.logger.debug(f"Closed position: {trade.symbol} P&L: ${trade.pnl:.2f}")

            # Generate AI decision
            try:
                decision = await self.ai_provider.generate_trading_decision(
                    market_state=market_state,
                    base_prompt=self._build_backtest_prompt()
                )

                # Validate decision
                validation = self.risk_manager.validate_decision(decision, market_state)

                if validation.approved and decision.action != TradingAction.HOLD:
                    # Execute trade
                    trade = self._execute_backtest_trade(
                        timestamp=timestamp,
                        decision=decision,
                        historical_data=historical_data,
                        current_capital=current_capital
                    )

                    if trade:
                        open_positions[decision.symbol] = trade
                        # Deduct position cost from capital
                        position_value = trade.quantity * trade.entry_price
                        current_capital -= position_value / trade.leverage

            except Exception as e:
                self.logger.error(f"Error at timestamp {timestamp}: {e}")
                continue

            # Update total equity
            total_equity = current_capital
            for pos_symbol, pos_trade in open_positions.items():
                current_price = historical_data[pos_symbol].loc[timestamp, 'close']
                unrealized_pnl = self._calculate_pnl(pos_trade, current_price)
                total_equity += unrealized_pnl

        # Close any remaining positions
        final_timestamp = timestamps[-1]
        for symbol, trade in list(open_positions.items()):
            final_price = historical_data[symbol].loc[final_timestamp, 'close']
            trade = self._close_trade(trade, final_price, "Backtest end")
            trades.append(trade)

        # Calculate performance metrics
        performance = self._calculate_performance(trades, initial_capital)

        self.logger.info("=" * 80)
        self.logger.info("📊 Backtest Complete")
        self.logger.info("=" * 80)
        self.logger.info(f"Total Trades: {len(trades)}")
        self.logger.info(f"Win Rate: {performance.win_rate:.1f}%")
        self.logger.info(f"Total P&L: ${performance.total_pnl:+.2f}")
        self.logger.info(f"Sharpe Ratio: {performance.sharpe_ratio:.2f}")
        self.logger.info(f"Max Drawdown: {performance.max_drawdown_percent:.1f}%")
        self.logger.info("=" * 80)

        # Generate AI insights
        self.logger.info("🧠 Generating AI insights on backtest results...")
        ai_insights = await self._generate_backtest_insights(trades, performance, strategy_name)

        return BacktestResult(
            period_start=start_ts,
            period_end=end_ts,
            trades=trades,
            performance=performance,
            ai_insights=ai_insights,
            strategy_name=strategy_name
        )

    def _build_market_state(
        self,
        timestamp: pd.Timestamp,
        historical_data: Dict[str, pd.DataFrame],
        current_capital: float,
        total_equity: float,
        open_positions: Dict[str, TradeRecord]
    ) -> MarketState:
        """Build market state from historical data at specific timestamp"""

        # Build account state
        account = AccountState(
            available_balance=current_capital,
            total_equity=total_equity,
            margin_used=total_equity - current_capital,
            margin_ratio=0.0 if total_equity == 0 else (total_equity - current_capital) / total_equity
        )

        # Build market snapshots for each symbol
        market_data_dict = {}
        for symbol, df in historical_data.items():
            if timestamp not in df.index:
                continue

            row = df.loc[timestamp]
            prev_row = df.loc[:timestamp].iloc[-2] if len(df.loc[:timestamp]) > 1 else row

            # Calculate indicators (simple versions)
            lookback = df.loc[:timestamp].tail(100)
            close_prices = lookback['close'].values

            from .indicators import calculate_rsi, calculate_macd, calculate_sma

            rsi = calculate_rsi(close_prices.tolist(), 14) if len(close_prices) >= 14 else None
            sma_20 = calculate_sma(close_prices.tolist(), 20) if len(close_prices) >= 20 else None
            sma_50 = calculate_sma(close_prices.tolist(), 50) if len(close_prices) >= 50 else None

            from .types import TechnicalIndicators
            indicators = TechnicalIndicators(
                rsi=rsi,
                sma_20=sma_20,
                sma_50=sma_50
            )

            snapshot = MarketSnapshot(
                symbol=symbol,
                timestamp=int(timestamp.timestamp() * 1000),
                current_price=float(row['close']),
                high_24h=float(lookback['high'].max()),
                low_24h=float(lookback['low'].min()),
                volume_24h=float(lookback['volume'].sum()),
                price_change_24h=float((row['close'] - prev_row['close']) / prev_row['close'] * 100),
                funding_rate=0.0,  # Not available in historical data
                open_interest=0.0,  # Not available in historical data
                indicators=indicators
            )

            market_data_dict[symbol] = snapshot

        # Build positions list
        from .types import Position
        positions = []
        for symbol, trade in open_positions.items():
            current_price = historical_data[symbol].loc[timestamp, 'close']
            unrealized_pnl = self._calculate_pnl(trade, current_price)
            unrealized_pnl_percent = (unrealized_pnl / (trade.quantity * trade.entry_price)) * 100 * trade.leverage

            positions.append(Position(
                symbol=symbol,
                side='long' if trade.action in [TradingAction.OPEN_LONG, TradingAction.BUY] else 'short',
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                current_price=current_price,
                leverage=trade.leverage,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_percent=unrealized_pnl_percent
            ))

        return MarketState(
            timestamp=int(timestamp.timestamp() * 1000),
            market_data=market_data_dict,
            account=account,
            positions=positions,
            performance_metrics=None  # No historical performance in backtest
        )

    def _execute_backtest_trade(
        self,
        timestamp: pd.Timestamp,
        decision: TradingDecision,
        historical_data: Dict[str, pd.DataFrame],
        current_capital: float
    ) -> Optional[TradeRecord]:
        """Execute a trade in the backtest simulation"""

        try:
            entry_price = historical_data[decision.symbol].loc[timestamp, 'close']

            # Calculate position size
            position_value = current_capital * (decision.quantity / 100)  # quantity is percentage
            quantity = position_value / entry_price

            trade = TradeRecord(
                timestamp=int(timestamp.timestamp() * 1000),
                symbol=decision.symbol,
                action=decision.action,
                quantity=quantity,
                leverage=decision.leverage,
                entry_price=entry_price,
                confidence=decision.confidence,
                reasoning=decision.reasoning,
                exit_plan=decision.exit_plan,
                status='open'
            )

            return trade

        except Exception as e:
            self.logger.error(f"Error executing backtest trade: {e}")
            return None

    def _check_exits(
        self,
        timestamp: pd.Timestamp,
        historical_data: Dict[str, pd.DataFrame],
        open_positions: Dict[str, TradeRecord]
    ) -> List[TradeRecord]:
        """Check if any positions hit exit conditions"""

        closed_trades = []

        for symbol in list(open_positions.keys()):
            trade = open_positions[symbol]

            if symbol not in historical_data or timestamp not in historical_data[symbol].index:
                continue

            current_price = historical_data[symbol].loc[timestamp, 'close']
            pnl_percent = self._calculate_pnl_percent(trade, current_price)

            should_close = False
            close_reason = None

            # Check stop-loss
            if pnl_percent <= -trade.exit_plan.stop_loss:
                should_close = True
                close_reason = f"Stop-loss: {pnl_percent:.2f}%"

            # Check take-profit
            elif pnl_percent >= trade.exit_plan.take_profit:
                should_close = True
                close_reason = f"Take-profit: {pnl_percent:.2f}%"

            if should_close:
                closed_trade = self._close_trade(trade, current_price, close_reason, timestamp)
                closed_trades.append(closed_trade)
                del open_positions[symbol]

        return closed_trades

    def _close_trade(
        self,
        trade: TradeRecord,
        exit_price: float,
        close_reason: str,
        timestamp: Optional[pd.Timestamp] = None
    ) -> TradeRecord:
        """Close a trade and calculate final P&L"""

        trade.exit_price = exit_price
        trade.exit_timestamp = int(timestamp.timestamp() * 1000) if timestamp else trade.timestamp + 1000
        trade.close_reason = close_reason
        trade.duration = trade.exit_timestamp - trade.timestamp
        trade.status = 'closed'

        # Calculate P&L
        trade.pnl = self._calculate_pnl(trade, exit_price)
        trade.pnl_percent = self._calculate_pnl_percent(trade, exit_price)

        return trade

    def _calculate_pnl(self, trade: TradeRecord, current_price: float) -> float:
        """Calculate P&L in USD"""
        position_value = trade.quantity * trade.entry_price

        if trade.action in [TradingAction.OPEN_LONG, TradingAction.BUY]:
            price_change = (current_price - trade.entry_price) / trade.entry_price
        else:  # SHORT
            price_change = (trade.entry_price - current_price) / trade.entry_price

        return position_value * price_change * trade.leverage

    def _calculate_pnl_percent(self, trade: TradeRecord, current_price: float) -> float:
        """Calculate P&L as percentage"""
        if trade.action in [TradingAction.OPEN_LONG, TradingAction.BUY]:
            price_change_pct = (current_price - trade.entry_price) / trade.entry_price * 100
        else:
            price_change_pct = (trade.entry_price - current_price) / trade.entry_price * 100

        return price_change_pct * trade.leverage

    def _calculate_performance(
        self,
        trades: List[TradeRecord],
        initial_capital: float
    ) -> PerformanceMetrics:
        """Calculate performance metrics from trades"""

        if not trades:
            return PerformanceMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl=0.0,
                total_pnl_percent=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_percent=0.0,
                profit_factor=0.0,
                average_win=0.0,
                average_loss=0.0,
                daily_pnl=0.0,
                daily_pnl_percent=0.0
            )

        winning_trades = [t for t in trades if (t.pnl or 0) > 0]
        losing_trades = [t for t in trades if (t.pnl or 0) < 0]

        total_pnl = sum(t.pnl or 0 for t in trades)
        gross_profit = sum(t.pnl for t in winning_trades)
        gross_loss = abs(sum(t.pnl for t in losing_trades))

        # Calculate returns for Sharpe ratio
        returns = [t.pnl_percent / 100 for t in trades if t.pnl_percent is not None]
        sharpe = 0.0
        if returns and np.std(returns) > 0:
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252)  # Annualized

        # Calculate max drawdown
        equity_curve = [initial_capital]
        for trade in trades:
            equity_curve.append(equity_curve[-1] + (trade.pnl or 0))

        peak = equity_curve[0]
        max_dd = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        return PerformanceMetrics(
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=(len(winning_trades) / len(trades)) * 100,
            total_pnl=total_pnl,
            total_pnl_percent=(total_pnl / initial_capital) * 100,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            max_drawdown_percent=(max_dd / initial_capital) * 100,
            profit_factor=gross_profit / gross_loss if gross_loss > 0 else 0,
            average_win=gross_profit / len(winning_trades) if winning_trades else 0,
            average_loss=gross_loss / len(losing_trades) if losing_trades else 0,
            daily_pnl=0.0,
            daily_pnl_percent=0.0
        )

    def _build_backtest_prompt(self) -> str:
        """Build system prompt for backtest mode"""
        return """You are analyzing historical market data for backtesting purposes.

Make trading decisions as you would in live trading, but be aware this is historical data.
Your decisions will be evaluated to see how the strategy performs over time.

Focus on:
- Consistent application of your trading philosophy
- Risk management discipline
- Pattern recognition
- Adapting to changing market conditions

Your performance in this backtest will be analyzed to improve future live trading."""

    async def _generate_backtest_insights(
        self,
        trades: List[TradeRecord],
        performance: PerformanceMetrics,
        strategy_name: str
    ) -> str:
        """Use LLM to generate insights from backtest results"""

        self.logger.info("Requesting AI analysis of backtest results...")

        # Build comprehensive context for AI
        context = f"""# Backtest Analysis Request

## Strategy: {strategy_name}

## Performance Summary
- Total Trades: {performance.total_trades}
- Win Rate: {performance.win_rate:.1f}%
- Total P&L: ${performance.total_pnl:+.2f} ({performance.total_pnl_percent:+.1f}%)
- Sharpe Ratio: {performance.sharpe_ratio:.2f}
- Max Drawdown: {performance.max_drawdown_percent:.1f}%
- Profit Factor: {performance.profit_factor:.2f}
- Average Win: ${performance.average_win:.2f}
- Average Loss: ${performance.average_loss:.2f}

## Trade Sample (First 10)
"""

        for i, trade in enumerate(trades[:10]):
            pnl_sign = '+' if (trade.pnl or 0) >= 0 else ''
            context += f"{i+1}. {trade.symbol} {trade.action.value}: "
            context += f"{pnl_sign}${trade.pnl:.2f} ({pnl_sign}{trade.pnl_percent:.2f}%) - "
            context += f"{trade.reasoning[:100]}...\n"

        context += f"\n...and {len(trades) - 10} more trades.\n\n"

        context += """
## Analysis Request

Please analyze these backtest results and provide:

1. **Overall Assessment**: Is this a viable trading strategy?
2. **Strengths**: What worked well?
3. **Weaknesses**: What needs improvement?
4. **Market Conditions**: What market conditions favor this strategy?
5. **Risk Analysis**: Is the risk/reward acceptable?
6. **Recommendations**: How can this strategy be improved?
7. **Forward-Looking**: What should be watched in live trading?

Be specific and actionable. This analysis will guide real trading decisions.
"""

        try:
            response = self.ai_provider.client.messages.create(
                model=self.ai_provider.config.model,
                max_tokens=2000,
                temperature=0.7,
                system="You are an expert quantitative analyst reviewing backt test results.",
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )

            insights = response.content[0].text
            self.logger.info("AI insights generated successfully")
            return insights

        except Exception as e:
            self.logger.error(f"Failed to generate AI insights: {e}")
            return f"Error generating insights: {e}"


async def load_historical_data(
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    timeframe: str = '1h'
) -> Dict[str, pd.DataFrame]:
    """
    Load historical data for backtesting.

    In production, this would fetch from exchange API or local database.
    For now, returns simulated data.
    """

    # TODO: Implement actual data loading from exchange or CSV
    # For now, return empty dict - implement this based on data source
    raise NotImplementedError(
        "Historical data loading not yet implemented. "
        "Please implement load_historical_data() to fetch OHLCV data from your data source."
    )
