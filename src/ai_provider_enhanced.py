"""
Enhanced AI Provider with Memory and Learning
Integrates memory system, post-trade analysis, and dynamic prompts
"""

from typing import Optional
import anthropic
from .types import (
    TradingDecision,
    MarketState,
    PerformanceMetrics,
    TradeRecord,
    TradingAction,
    ExitPlan
)
from .ai_provider import AIProvider
from .memory_system import MemorySystem
from .post_trade_analysis import PostTradeAnalyzer
from .dynamic_prompt import DynamicPromptBuilder, select_prompt_mode
from .database import TradingDatabase
from .config import AIConfig
import json
import logging


class EnhancedAnthropicProvider(AIProvider):
    """
    Enhanced AI provider with memory, learning, and dynamic prompts.

    This provider extends the base AI functionality with:
    - Dual-layer memory system (short-term and long-term)
    - Post-trade analysis and learning
    - Dynamic prompt evolution based on performance
    - Personality trait tracking and adaptation
    """

    def __init__(
        self,
        config: AIConfig,
        database: TradingDatabase,
        logger: Optional[logging.Logger] = None
    ):
        super().__init__(config, logger)

        self.database = database
        self.memory_system = MemorySystem(database)
        self.post_trade_analyzer = PostTradeAnalyzer(database)
        self.prompt_builder = DynamicPromptBuilder()

        self.logger.info("Enhanced AI provider initialized with memory and learning capabilities")

    async def generate_trading_decision(
        self,
        market_state: MarketState,
        base_prompt: str
    ) -> TradingDecision:
        """
        Generate trading decision with full memory and learning integration.

        This method:
        1. Loads short-term and long-term memory
        2. Selects appropriate prompt mode based on performance
        3. Builds evolved prompt with personality adaptations
        4. Injects memory context into AI decision
        5. Generates decision with self-awareness
        """

        try:
            # Step 1: Load memory
            self.logger.info("Loading AI memory...")
            short_term_memory = await self.memory_system.build_short_term_memory(limit=10)
            long_term_memory = await self.memory_system.build_long_term_memory()

            # Step 2: Determine prompt mode based on performance
            performance = market_state.performance_metrics
            prompt_mode = select_prompt_mode(performance)
            self.logger.info(f"Selected prompt mode: {prompt_mode}")

            # Step 3: Build evolved prompt
            if prompt_mode == 'crisis':
                evolved_prompt = base_prompt + "\n\n" + self.prompt_builder.create_crisis_prompt()
                self.logger.warning("⚠️ CRISIS MODE ACTIVATED - Defensive trading parameters in effect")
            elif prompt_mode == 'fresh':
                evolved_prompt = base_prompt + "\n\n" + self.prompt_builder.create_fresh_perspective_prompt()
                self.logger.info("🔄 Fresh perspective mode - Resetting cognitive biases")
            else:
                # Normal mode with performance-based evolution
                evolved_prompt = self.prompt_builder.build_evolving_prompt(
                    base_prompt,
                    performance,
                    long_term_memory.personality_traits if long_term_memory else None
                )

            # Step 4: Format memory for AI context
            memory_context = self.memory_system.format_memory_for_ai(
                short_term_memory,
                long_term_memory
            )

            # Step 5: Build complete context with market data
            market_context = self._format_market_context(market_state)

            # Combine all context
            full_context = f"""
{memory_context}

{market_context}

---

Based on your memory, personality, and the current market conditions above, make your trading decision.
Remember to include your self-reflection on your current mental state and any biases you notice.
"""

            # Step 6: Generate decision from Claude
            self.logger.info("Generating AI trading decision with full context...")
            decision = await self._call_claude_api(evolved_prompt, full_context)

            # Step 7: Log decision quality metrics
            self._log_decision_quality(decision, prompt_mode, long_term_memory)

            return decision

        except Exception as e:
            self.logger.error(f"Error in enhanced decision generation: {e}")
            raise

    def _format_market_context(self, market_state: MarketState) -> str:
        """Format market state into readable context for AI"""

        context = "# CURRENT MARKET CONDITIONS\n\n"

        # Account status
        context += f"## Your Trading Account\n"
        context += f"- Available Balance: ${market_state.account.available_balance:.2f}\n"
        context += f"- Total Equity: ${market_state.account.total_equity:.2f}\n"
        context += f"- Open Positions: {len(market_state.positions)}\n"
        context += f"- Margin Ratio: {market_state.account.margin_ratio * 100:.1f}%\n\n"

        # Current positions
        if market_state.positions:
            context += "## Your Open Positions\n"
            for pos in market_state.positions:
                pnl_sign = "+" if pos.unrealized_pnl >= 0 else ""
                context += f"- {pos.symbol}: {pos.side} {pos.quantity} contracts @ ${pos.entry_price:.2f}\n"
                context += f"  Leverage: {pos.leverage}x | P&L: {pnl_sign}${pos.unrealized_pnl:.2f} ({pnl_sign}{pos.unrealized_pnl_percent:.2f}%)\n"
            context += "\n"

        # Market data for each symbol
        context += "## Available Trading Opportunities\n\n"
        for symbol, snapshot in market_state.market_data.items():
            context += f"### {symbol}\n"
            context += f"- Price: ${snapshot.current_price:.2f}\n"
            context += f"- 24h Change: {snapshot.price_change_24h:+.2f}%\n"
            context += f"- Volume: ${snapshot.volume_24h:,.0f}\n"

            if snapshot.indicators:
                ind = snapshot.indicators
                context += f"- **Technical Indicators:**\n"
                if ind.rsi:
                    context += f"  - RSI(14): {ind.rsi:.1f}"
                    if ind.rsi > 70:
                        context += " (OVERBOUGHT)\n"
                    elif ind.rsi < 30:
                        context += " (OVERSOLD)\n"
                    else:
                        context += "\n"

                if ind.macd and ind.macd_signal:
                    macd_trend = "BULLISH" if ind.macd > ind.macd_signal else "BEARISH"
                    context += f"  - MACD: {ind.macd:.4f} | Signal: {ind.macd_signal:.4f} ({macd_trend})\n"

                if ind.bb_upper and ind.bb_lower:
                    context += f"  - Bollinger Bands: ${ind.bb_lower:.2f} - ${ind.bb_upper:.2f}\n"
                    if snapshot.current_price > ind.bb_upper:
                        context += f"    Price ABOVE upper band (overbought zone)\n"
                    elif snapshot.current_price < ind.bb_lower:
                        context += f"    Price BELOW lower band (oversold zone)\n"

                if ind.atr:
                    context += f"  - ATR(14): ${ind.atr:.2f} (volatility indicator)\n"

            context += "\n"

        # Performance context
        if market_state.performance_metrics:
            perf = market_state.performance_metrics
            context += "## Your Recent Performance\n"
            context += f"- Total Trades: {perf.total_trades}\n"
            context += f"- Win Rate: {perf.win_rate:.1f}%\n"
            context += f"- Total P&L: ${perf.total_pnl:+.2f}\n"
            context += f"- Sharpe Ratio: {perf.sharpe_ratio:.2f}\n"
            context += f"- Max Drawdown: {perf.max_drawdown_percent:.1f}%\n"
            context += f"- Today's P&L: {perf.daily_pnl_percent:+.2f}%\n\n"

        return context

    async def _call_claude_api(self, system_prompt: str, user_message: str) -> TradingDecision:
        """Call Claude API with enhanced prompts and parse decision"""

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )

            response_text = response.content[0].text
            self.logger.debug(f"Claude response: {response_text[:200]}...")

            # Parse JSON response
            decision_data = self._extract_json_from_response(response_text)

            # Convert to TradingDecision
            decision = TradingDecision(
                action=TradingAction(decision_data['action']),
                symbol=decision_data['symbol'],
                quantity=decision_data['quantity'],
                leverage=decision_data['leverage'],
                confidence=decision_data['confidence'],
                reasoning=decision_data['reasoning'],
                exit_plan=ExitPlan(**decision_data['exit_plan']),
                self_reflection=decision_data.get('self_reflection')
            )

            return decision

        except Exception as e:
            self.logger.error(f"Error calling Claude API: {e}")
            raise

    def _extract_json_from_response(self, response_text: str) -> dict:
        """Extract JSON from Claude's response (may be wrapped in markdown)"""

        # Try to find JSON in markdown code block
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            json_text = response_text[start:end].strip()
        else:
            # Assume entire response is JSON
            json_text = response_text.strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.error(f"Response text: {response_text}")
            raise

    def _log_decision_quality(
        self,
        decision: TradingDecision,
        prompt_mode: str,
        long_term_memory
    ):
        """Log decision quality metrics for monitoring"""

        self.logger.info(f"Decision generated: {decision.action.value} {decision.symbol}")
        self.logger.info(f"Confidence: {decision.confidence * 100:.0f}% | Leverage: {decision.leverage}x")
        self.logger.info(f"Prompt mode: {prompt_mode}")

        if decision.self_reflection:
            self.logger.info(f"AI self-reflection: {decision.self_reflection[:100]}...")

        if long_term_memory and long_term_memory.personality_traits:
            personality = long_term_memory.personality_traits
            self.logger.debug(f"AI personality: Risk={personality.risk_tolerance:.2f}, "
                            f"Patience={personality.patience:.2f}, "
                            f"Confidence={personality.confidence_level:.2f}")

    async def analyze_completed_trade(self, trade: TradeRecord) -> None:
        """
        Analyze a completed trade and store learnings.
        This is called after a trade is closed to extract insights.
        """

        try:
            self.logger.info(f"Analyzing completed trade #{trade.id}...")

            # Generate analysis
            analysis = self.post_trade_analyzer.analyze_trade(trade)

            # Log key insights
            self.logger.info(f"Trade outcome: {analysis.outcome}")
            self.logger.info(f"Key takeaways: {len(analysis.key_takeaways)}")

            for takeaway in analysis.key_takeaways:
                self.logger.info(f"  - {takeaway}")

            if analysis.emotional_factors:
                self.logger.warning("Emotional factors detected:")
                for factor in analysis.emotional_factors:
                    self.logger.warning(f"  - {factor}")

            # Store analysis in database
            await self.database.store_trade_analysis(analysis)

            # Store lessons in long-term memory
            for lesson in analysis.recommendations:
                await self.memory_system.store_lesson(
                    content=lesson,
                    trade_id=trade.id,
                    category='recommendation',
                    importance=0.7
                )

            self.logger.info("Trade analysis complete and stored in memory")

        except Exception as e:
            self.logger.error(f"Error analyzing trade: {e}")

    async def generate_session_report(self, from_timestamp: int, to_timestamp: int) -> str:
        """Generate comprehensive analysis of a trading session"""

        return self.post_trade_analyzer.analyze_trading_session(
            from_timestamp,
            to_timestamp
        )
