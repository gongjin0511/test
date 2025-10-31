"""
Enhanced Trading Orchestrator with Memory and Learning
Extends base orchestrator with continuity features
"""

import asyncio
import time
from typing import Dict, Optional
from .types import MarketState, TradingDecision, DecisionRecord, TradeRecord, TradingAction
from .config import SystemConfig
from .database import TradingDatabase
from .exchange_client import OKXClient
from .ai_provider_enhanced import EnhancedAnthropicProvider
from .risk_manager import RiskManager
from .orchestrator import TradingOrchestrator
import logging


class EnhancedTradingOrchestrator(TradingOrchestrator):
    """
    Enhanced trading orchestrator with memory and learning capabilities.

    Extends the base orchestrator with:
    - Memory persistence and recall between decisions
    - Post-trade analysis and learning
    - Dynamic prompt evolution
    - Personality trait tracking
    - Session-based learning and reports
    """

    def __init__(
        self,
        config: SystemConfig,
        exchange: OKXClient,
        ai_provider: EnhancedAnthropicProvider,  # Enhanced provider
        risk_manager: RiskManager,
        database: TradingDatabase,
        system_prompt: str,
        logger: Optional[logging.Logger] = None,
        sentiment_aggregator: Optional[any] = None  # Optional sentiment aggregator
    ):
        # Initialize base orchestrator
        super().__init__(
            config=config,
            exchange=exchange,
            ai_provider=ai_provider,
            risk_manager=risk_manager,
            database=database,
            system_prompt=system_prompt
        )

        self.logger = logger or logging.getLogger(__name__)
        self.session_start_time: Optional[int] = None
        self.trades_this_session: int = 0
        self.sentiment_aggregator = sentiment_aggregator

        # Override ai_provider type for better type checking
        self.ai_provider: EnhancedAnthropicProvider = ai_provider

    async def start(self):
        """Start the enhanced trading system"""

        self.session_start_time = int(time.time() * 1000)

        self.logger.info("=" * 80)
        self.logger.info("🚀 Starting Enhanced AI Trading System")
        self.logger.info("=" * 80)
        self.logger.info("Features enabled:")
        self.logger.info("  ✅ Dual-layer memory system (short-term + long-term)")
        self.logger.info("  ✅ Dynamic prompt evolution (normal/crisis/fresh modes)")
        self.logger.info("  ✅ Post-trade analysis and learning")
        self.logger.info("  ✅ Personality trait tracking")
        self.logger.info("  ✅ Emotional factor detection")
        self.logger.info("=" * 80)

        # Load existing memory to show context
        short_term = await self.ai_provider.memory_system.build_short_term_memory(limit=5)
        long_term = await self.ai_provider.memory_system.build_long_term_memory()

        self.logger.info(f"📚 Memory loaded:")
        self.logger.info(f"  - Recent trades: {len(short_term.recent_trades)}")
        self.logger.info(f"  - Lessons learned: {len(long_term.lessons) if long_term else 0}")
        self.logger.info(f"  - Patterns recognized: {len(long_term.patterns) if long_term else 0}")

        if long_term and long_term.personality_traits:
            personality = long_term.personality_traits
            self.logger.info(f"  - Trading personality: {personality.trading_philosophy}")
            self.logger.info(f"    Risk tolerance: {personality.risk_tolerance:.2f}")
            self.logger.info(f"    Patience level: {personality.patience:.2f}")
            self.logger.info(f"    Confidence: {personality.confidence_level:.2f}")

        # Call base start
        await super().start()

    async def stop(self):
        """Stop the enhanced trading system and generate session report"""

        if self.session_start_time:
            self.logger.info("=" * 80)
            self.logger.info("📊 Generating session report...")
            self.logger.info("=" * 80)

            # Generate session report
            try:
                report = await self.ai_provider.generate_session_report(
                    from_timestamp=self.session_start_time,
                    to_timestamp=int(time.time() * 1000)
                )

                self.logger.info(report)

            except Exception as e:
                self.logger.error(f"Failed to generate session report: {e}")

        # Call base stop
        await super().stop()

    async def _run_decision_cycle(self):
        """
        Run enhanced decision cycle with memory and learning.

        Enhanced cycle flow:
        1. Collect market data (includes performance metrics)
        2. Generate AI decision (with memory context)
        3. Validate with risk management
        4. Execute if approved
        5. Monitor and analyze completed trades
        6. Update memory and learning
        """

        cycle_start = time.time()

        self.logger.info("━" * 80)
        self.logger.info("🔄 Starting Enhanced Decision Cycle")
        self.logger.info("━" * 80)

        try:
            # Step 1: Collect market data
            self.logger.info("📊 Collecting market data...")
            market_state = await self._collect_market_data()

            # Step 1.5: Add news sentiment context if available
            news_context = ""
            if self.sentiment_aggregator:
                news_context = await self._build_news_context(market_state)

            # Step 2: Generate AI decision (with enhanced provider)
            self.logger.info("🧠 Generating AI decision with memory and news context...")
            ai_start = time.time()

            # Build enhanced prompt with news context
            enhanced_prompt = self.system_prompt
            if news_context:
                enhanced_prompt = f"{self.system_prompt}\n\n{news_context}"

            # Enhanced provider automatically loads memory and selects prompt mode
            decision = await self.ai_provider.generate_trading_decision(
                market_state=market_state,
                base_prompt=enhanced_prompt
            )

            ai_time = int((time.time() - ai_start) * 1000)

            self.logger.info("✅ AI decision generated:")
            self.logger.info(f"   Action: {decision.action.value}")
            self.logger.info(f"   Symbol: {decision.symbol}")
            self.logger.info(f"   Confidence: {decision.confidence * 100:.0f}%")
            self.logger.info(f"   Leverage: {decision.leverage}x")
            self.logger.info(f"   Reasoning: {decision.reasoning[:100]}...")

            if decision.self_reflection:
                self.logger.info(f"   Self-reflection: {decision.self_reflection[:100]}...")

            # Step 3: Validate with risk management
            self.logger.info("🛡️  Validating decision...")
            validation = self.risk_manager.validate_decision(decision, market_state)

            # Step 4: Save decision
            import json
            decision_record = DecisionRecord(
                timestamp=int(time.time() * 1000),
                market_state=json.dumps(market_state.model_dump(), default=str),
                ai_output=json.dumps(decision.model_dump(), default=str),
                risk_approved=validation.approved,
                rejection_reason=validation.reason,
                execution_time=ai_time
            )
            self.database.save_decision(decision_record)

            # Step 5: Execute if approved
            if validation.approved:
                self.logger.info("✅ Decision approved by risk manager")

                # Execute trade (if not HOLD)
                if decision.action != TradingAction.HOLD:
                    await self._execute_trade(decision, market_state)
                else:
                    self.logger.info("   AI decided to HOLD - no action taken")
            else:
                self.logger.warning(f"❌ Decision rejected: {validation.reason}")

            # Step 6: Monitor and analyze completed trades
            await self._check_and_analyze_completed_trades()

            cycle_time = int((time.time() - cycle_start) * 1000)
            self.logger.info("━" * 80)
            self.logger.info(f"✅ Enhanced decision cycle completed in {cycle_time}ms")
            self.logger.info("━" * 80)

        except Exception as e:
            self.logger.error(f"❌ Error in enhanced decision cycle: {e}", exc_info=True)
            raise

    async def _execute_trade(self, decision: TradingDecision, market_state: MarketState):
        """
        Execute approved trade and create trade record.

        In production, this would:
        1. Place order via exchange API
        2. Monitor order execution
        3. Create position tracking
        4. Set up stop-loss and take-profit orders
        """

        self.logger.info(f"💰 Executing trade: {decision.action.value} {decision.symbol}")

        try:
            # In demo mode, we simulate trade execution
            # In production, call: await self.exchange.place_order(...)

            # Create trade record
            trade_record = TradeRecord(
                timestamp=int(time.time() * 1000),
                symbol=decision.symbol,
                action=decision.action,
                quantity=decision.quantity,
                leverage=decision.leverage,
                entry_price=market_state.market_data[decision.symbol].current_price,
                confidence=decision.confidence,
                reasoning=decision.reasoning,
                exit_plan=decision.exit_plan,
                status='open'
            )

            # Save to database
            trade_id = self.database.save_trade(trade_record)
            self.trades_this_session += 1

            self.logger.info(f"✅ Trade #{trade_id} created and tracked")
            self.logger.info(f"   Entry: ${trade_record.entry_price:.2f}")
            self.logger.info(f"   Stop-loss: {decision.exit_plan.stop_loss}%")
            self.logger.info(f"   Take-profit: {decision.exit_plan.take_profit}%")

            # In production: Set up monitoring for exit conditions
            # For now, we'll check exit conditions in _check_and_analyze_completed_trades

        except Exception as e:
            self.logger.error(f"Failed to execute trade: {e}")
            raise

    async def _check_and_analyze_completed_trades(self):
        """
        Check for trades that hit exit conditions and analyze them.

        This method:
        1. Checks all open positions for exit conditions
        2. Closes positions that hit stop-loss or take-profit
        3. Analyzes completed trades
        4. Stores learnings in memory
        """

        try:
            # Get all open trades
            open_trades = self.database.get_trades(status='open')

            if not open_trades:
                return

            # Get current market data
            for trade in open_trades:
                try:
                    # Get current price
                    market_data = await self.exchange.get_market_data(trade.symbol)
                    current_price = market_data.current_price

                    # Calculate P&L
                    if trade.action in [TradingAction.OPEN_LONG, TradingAction.BUY]:
                        pnl_percent = ((current_price - trade.entry_price) / trade.entry_price) * 100 * trade.leverage
                    else:  # SHORT
                        pnl_percent = ((trade.entry_price - current_price) / trade.entry_price) * 100 * trade.leverage

                    # Check exit conditions
                    should_close = False
                    close_reason = None

                    if pnl_percent <= -trade.exit_plan.stop_loss:
                        should_close = True
                        close_reason = f"Stop-loss hit: {pnl_percent:.2f}%"
                    elif pnl_percent >= trade.exit_plan.take_profit:
                        should_close = True
                        close_reason = f"Take-profit hit: {pnl_percent:.2f}%"
                    elif trade.exit_plan.trailing_stop and pnl_percent > 5:
                        # Simple trailing stop logic
                        # In production: track highest price and trail stop-loss
                        pass

                    if should_close:
                        await self._close_trade(trade, current_price, close_reason)

                except Exception as e:
                    self.logger.error(f"Error checking trade #{trade.id}: {e}")

        except Exception as e:
            self.logger.error(f"Error in completed trades check: {e}")

    async def _close_trade(self, trade: TradeRecord, exit_price: float, close_reason: str):
        """Close a trade and analyze it"""

        self.logger.info(f"🔚 Closing trade #{trade.id}: {close_reason}")

        try:
            # Calculate final P&L
            if trade.action in [TradingAction.OPEN_LONG, TradingAction.BUY]:
                pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100 * trade.leverage
            else:
                pnl_percent = ((trade.entry_price - exit_price) / trade.entry_price) * 100 * trade.leverage

            # Assuming $1000 position size for demo
            position_value = trade.quantity * trade.entry_price
            pnl_usd = position_value * (pnl_percent / 100)

            # Update trade record
            trade.status = 'closed'
            trade.exit_price = exit_price
            trade.exit_timestamp = int(time.time() * 1000)
            trade.pnl = pnl_usd
            trade.pnl_percent = pnl_percent
            trade.close_reason = close_reason
            trade.duration = trade.exit_timestamp - trade.timestamp

            # Save updated trade
            self.database.update_trade(trade)

            pnl_sign = "+" if pnl_usd >= 0 else ""
            self.logger.info(f"✅ Trade closed:")
            self.logger.info(f"   Entry: ${trade.entry_price:.2f}")
            self.logger.info(f"   Exit: ${exit_price:.2f}")
            self.logger.info(f"   P&L: {pnl_sign}${pnl_usd:.2f} ({pnl_sign}{pnl_percent:.2f}%)")
            self.logger.info(f"   Duration: {trade.duration / (1000 * 60):.1f} minutes")

            # Analyze the trade
            self.logger.info("🔍 Analyzing trade for learnings...")
            await self.ai_provider.analyze_completed_trade(trade)

            self.logger.info("✅ Trade analysis complete and stored in memory")

        except Exception as e:
            self.logger.error(f"Error closing trade: {e}")
            raise

    async def _collect_market_data(self) -> MarketState:
        """Collect enhanced market data including positions"""

        # Get account state
        account = await self.exchange.get_account_state()

        # Get current positions (from database in demo, from exchange in production)
        open_trades = self.database.get_trades(status='open')
        positions = []

        for trade in open_trades:
            try:
                # Get current market data for position
                market_data = await self.exchange.get_market_data(trade.symbol)
                current_price = market_data.current_price

                # Calculate unrealized P&L
                if trade.action in [TradingAction.OPEN_LONG, TradingAction.BUY]:
                    unrealized_pnl_percent = ((current_price - trade.entry_price) / trade.entry_price) * 100 * trade.leverage
                else:
                    unrealized_pnl_percent = ((trade.entry_price - current_price) / trade.entry_price) * 100 * trade.leverage

                position_value = trade.quantity * trade.entry_price
                unrealized_pnl = position_value * (unrealized_pnl_percent / 100)

                from .types import Position
                positions.append(Position(
                    symbol=trade.symbol,
                    side='long' if trade.action in [TradingAction.OPEN_LONG, TradingAction.BUY] else 'short',
                    quantity=trade.quantity,
                    entry_price=trade.entry_price,
                    current_price=current_price,
                    leverage=trade.leverage,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pnl_percent
                ))

            except Exception as e:
                self.logger.error(f"Error processing position for {trade.symbol}: {e}")

        # Get market data for all trading pairs
        market_data_dict: Dict = {}
        for symbol in self.config.trading.trading_pairs:
            try:
                market_snapshot = await self.exchange.get_market_data(symbol)
                market_data_dict[symbol] = market_snapshot
            except Exception as e:
                self.logger.error(f"Failed to get market data for {symbol}: {e}")

        # Get latest performance metrics
        performance = self.database.get_latest_performance()

        return MarketState(
            timestamp=int(time.time() * 1000),
            market_data=market_data_dict,
            account=account,
            positions=positions,
            performance_metrics=performance
        )

    async def _build_news_context(self, market_state: MarketState) -> str:
        """构建新闻和情绪上下文"""

        if not self.sentiment_aggregator:
            return ""

        context = "\n# 📰 实时新闻和市场情绪\n\n"

        try:
            # 为每个交易对添加情绪信息
            for symbol in self.config.trading.trading_pairs:
                symbol_short = symbol.split('-')[0]

                # 获取最新情绪
                avg_sentiment = self.sentiment_aggregator.get_average_sentiment(symbol_short, hours=6)
                trend = self.sentiment_aggregator.get_sentiment_trend(symbol_short, hours=6)

                if trend == "insufficient_data":
                    continue

                # 获取历史记录中最新的详细情绪
                if symbol_short in self.sentiment_aggregator.sentiment_history:
                    recent_sentiments = self.sentiment_aggregator.sentiment_history[symbol_short]
                    if recent_sentiments:
                        latest = recent_sentiments[-1]

                        context += f"## {symbol_short} 新闻情绪\n\n"

                        # 情绪评分和趋势
                        trend_emoji = {
                            "improving": "📈 改善中",
                            "declining": "📉 下降中",
                            "stable": "➡️ 稳定"
                        }

                        context += f"**当前情绪**: {latest.sentiment_score:+.2f} ({latest.sentiment_label})\n"
                        context += f"**6小时平均**: {avg_sentiment:+.2f}\n"
                        context += f"**趋势**: {trend_emoji.get(trend, trend)}\n"
                        context += f"**置信度**: {latest.confidence * 100:.0f}%\n\n"

                        # 关键主题
                        if latest.key_themes:
                            context += f"**关键主题**: {', '.join(latest.key_themes[:3])}\n\n"

                        # 重大事件
                        if latest.major_events:
                            context += f"**重大事件**:\n"
                            for event in latest.major_events[:3]:
                                context += f"- {event}\n"
                            context += "\n"

                        # 风险提示
                        if latest.risk_factors:
                            context += f"**⚠️ 风险因素**: {', '.join(latest.risk_factors[:2])}\n\n"

                        # 机会
                        if latest.opportunities:
                            context += f"**✅ 交易机会**: {', '.join(latest.opportunities[:2])}\n\n"

                        context += f"**情绪总结**: {latest.summary}\n\n"

            context += "---\n\n"
            context += "**重要提示**: 结合技术分析和新闻情绪做出决策。新闻情绪可能滞后或过度反应。\n"

            return context

        except Exception as e:
            self.logger.error(f"Error building news context: {e}")
            return ""
