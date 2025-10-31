"""
LLM-Powered Pattern Recognition
Uses AI to identify trading patterns and market behaviors
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import anthropic
from .types import TradeRecord, MarketSnapshot, Pattern
from .database import TradingDatabase
from .config import AIConfig
import logging
import json


class PatternRecognizer:
    """
    LLM-powered pattern recognition system.

    Instead of traditional ML models, this uses the LLM's reasoning
    capabilities to identify patterns in trading data.
    """

    def __init__(
        self,
        ai_config: AIConfig,
        database: TradingDatabase,
        logger: Optional[logging.Logger] = None
    ):
        self.config = ai_config
        self.database = database
        self.logger = logger or logging.getLogger(__name__)
        self.client = anthropic.Anthropic(api_key=ai_config.api_key)

    async def analyze_trading_patterns(
        self,
        lookback_days: int = 30
    ) -> List[Pattern]:
        """
        Analyze recent trading history to identify patterns.

        Uses LLM to discover:
        - Winning setups that repeat
        - Losing patterns to avoid
        - Market condition correlations
        - Time-of-day patterns
        - Symbol-specific behaviors
        """

        self.logger.info(f"🔍 Analyzing trading patterns (last {lookback_days} days)...")

        # Get recent trades
        cutoff = int((datetime.now() - timedelta(days=lookback_days)).timestamp() * 1000)
        trades = self.database.get_trades(from_timestamp=cutoff, status='closed')

        if len(trades) < 5:
            self.logger.warning("Insufficient trades for pattern analysis")
            return []

        # Prepare data for LLM analysis
        trades_summary = self._prepare_trades_summary(trades)

        # Ask LLM to identify patterns
        prompt = self._build_pattern_analysis_prompt(trades_summary, lookback_days)

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=2000,
                temperature=0.7,
                system="""You are an expert trading analyst specializing in pattern recognition.
Your task is to analyze trading history and identify recurring patterns.
Focus on actionable insights that can improve future trading decisions.""",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text
            self.logger.debug(f"LLM pattern analysis: {response_text[:200]}...")

            # Parse patterns from response
            patterns = self._parse_patterns_from_response(response_text, trades)

            self.logger.info(f"✅ Identified {len(patterns)} patterns")
            for pattern in patterns:
                self.logger.info(f"  - {pattern.pattern_type}: {pattern.description}")

            return patterns

        except Exception as e:
            self.logger.error(f"Error in pattern analysis: {e}")
            return []

    async def analyze_market_regime(
        self,
        symbol: str,
        market_data: List[MarketSnapshot]
    ) -> str:
        """
        Use LLM to identify current market regime.

        Returns description like:
        - "Strong uptrend with high momentum"
        - "Range-bound choppy market"
        - "Bearish reversal in progress"
        """

        if len(market_data) < 20:
            return "Insufficient data for regime analysis"

        # Prepare market data summary
        market_summary = self._prepare_market_summary(symbol, market_data)

        prompt = f"""Analyze the following market data and identify the current market regime.

{market_summary}

Describe the market regime in 1-2 sentences. Include:
- Trend direction (up/down/sideways)
- Volatility level (high/low/moderate)
- Momentum strength
- Any notable patterns

Be concise and actionable for trading decisions."""

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=300,
                temperature=0.5,
                system="You are a technical analyst identifying market regimes.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            regime = response.content[0].text.strip()
            self.logger.info(f"Market regime for {symbol}: {regime}")
            return regime

        except Exception as e:
            self.logger.error(f"Error analyzing market regime: {e}")
            return "Unknown regime - analysis failed"

    async def identify_trade_mistakes(
        self,
        recent_losses: List[TradeRecord]
    ) -> Dict[str, List[str]]:
        """
        Use LLM to identify common mistakes in losing trades.

        Returns categorized mistakes:
        {
            "entry_mistakes": ["Entered without confirmation", ...],
            "exit_mistakes": ["Held too long", ...],
            "risk_mistakes": ["Position too large", ...],
            "psychological": ["Revenge trading", ...]
        }
        """

        if not recent_losses:
            return {}

        losses_summary = self._prepare_trades_summary(recent_losses)

        prompt = f"""Analyze these LOSING trades and identify common mistakes:

{losses_summary}

Categorize the mistakes into:
1. Entry mistakes (wrong timing, no confirmation, etc.)
2. Exit mistakes (premature exit, holding too long, etc.)
3. Risk management mistakes (position sizing, leverage, etc.)
4. Psychological mistakes (FOMO, revenge trading, overconfidence, etc.)

Return as JSON:
{{
    "entry_mistakes": ["mistake 1", "mistake 2"],
    "exit_mistakes": ["mistake 1"],
    "risk_mistakes": ["mistake 1"],
    "psychological": ["mistake 1"]
}}"""

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=1000,
                temperature=0.7,
                system="You are a trading psychology expert identifying mistakes.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text

            # Extract JSON from response
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            else:
                json_text = response_text.strip()

            mistakes = json.loads(json_text)

            self.logger.info("Common mistakes identified:")
            for category, items in mistakes.items():
                self.logger.info(f"  {category}: {len(items)} mistakes")

            return mistakes

        except Exception as e:
            self.logger.error(f"Error identifying mistakes: {e}")
            return {}

    async def suggest_strategy_improvements(
        self,
        trades: List[TradeRecord],
        current_performance: Dict
    ) -> List[str]:
        """
        Use LLM to suggest strategy improvements based on performance.

        Returns list of actionable suggestions.
        """

        if len(trades) < 10:
            return ["Insufficient trading history for improvement suggestions"]

        trades_summary = self._prepare_trades_summary(trades)
        perf_summary = json.dumps(current_performance, indent=2)

        prompt = f"""Based on this trading history and performance, suggest 3-5 specific improvements:

## Performance Metrics
{perf_summary}

## Trade History
{trades_summary}

Provide actionable suggestions to improve the strategy. Be specific.
Each suggestion should address a concrete issue seen in the data.

Format as a simple list:
1. Suggestion one
2. Suggestion two
etc."""

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=800,
                temperature=0.7,
                system="You are a trading strategy consultant providing improvement recommendations.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text

            # Parse suggestions (extract numbered list)
            suggestions = []
            for line in response_text.split('\n'):
                line = line.strip()
                # Match patterns like "1. ", "1) ", "- ", etc.
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering/bullets
                    suggestion = line.lstrip('0123456789.-•) ').strip()
                    if suggestion:
                        suggestions.append(suggestion)

            self.logger.info(f"Strategy improvements suggested: {len(suggestions)}")
            for i, suggestion in enumerate(suggestions, 1):
                self.logger.info(f"  {i}. {suggestion[:100]}...")

            return suggestions

        except Exception as e:
            self.logger.error(f"Error generating suggestions: {e}")
            return []

    def _prepare_trades_summary(self, trades: List[TradeRecord]) -> str:
        """Prepare trades data for LLM analysis"""

        summary = f"Total Trades: {len(trades)}\n\n"

        for i, trade in enumerate(trades[:50], 1):  # Limit to 50 for context window
            pnl_sign = '+' if (trade.pnl or 0) >= 0 else ''
            outcome = "WIN" if (trade.pnl or 0) > 0 else "LOSS"

            summary += f"{i}. [{outcome}] {trade.symbol} {trade.action.value}\n"
            summary += f"   Entry: ${trade.entry_price:.2f} | Exit: ${trade.exit_price or 0:.2f}\n"
            summary += f"   P&L: {pnl_sign}${trade.pnl or 0:.2f} ({pnl_sign}{trade.pnl_percent or 0:.2f}%)\n"
            summary += f"   Leverage: {trade.leverage}x | Confidence: {trade.confidence * 100:.0f}%\n"
            summary += f"   Reasoning: {trade.reasoning[:150]}\n"

            if trade.duration:
                hours = trade.duration / (1000 * 60 * 60)
                summary += f"   Duration: {hours:.1f} hours\n"

            summary += f"   Exit: {trade.close_reason or 'N/A'}\n\n"

        if len(trades) > 50:
            summary += f"... and {len(trades) - 50} more trades\n"

        return summary

    def _prepare_market_summary(self, symbol: str, market_data: List[MarketSnapshot]) -> str:
        """Prepare market data for LLM analysis"""

        recent = market_data[-50:]  # Last 50 data points

        summary = f"Market Data for {symbol} (Last {len(recent)} timepoints)\n\n"

        prices = [m.current_price for m in recent]
        summary += f"Price Range: ${min(prices):.2f} - ${max(prices):.2f}\n"
        summary += f"Current Price: ${recent[-1].current_price:.2f}\n"
        summary += f"Change: {((recent[-1].current_price - recent[0].current_price) / recent[0].current_price * 100):+.2f}%\n\n"

        # Technical indicators from most recent
        if recent[-1].indicators:
            ind = recent[-1].indicators
            summary += "Technical Indicators:\n"
            if ind.rsi:
                summary += f"  RSI: {ind.rsi:.1f}\n"
            if ind.macd and ind.macd_signal:
                summary += f"  MACD: {ind.macd:.4f} / Signal: {ind.macd_signal:.4f}\n"
            if ind.sma_20 and ind.sma_50:
                summary += f"  SMA20: ${ind.sma_20:.2f} | SMA50: ${ind.sma_50:.2f}\n"

        summary += "\nRecent Price Action (last 10):\n"
        for m in recent[-10:]:
            ts = datetime.fromtimestamp(m.timestamp / 1000)
            summary += f"  {ts:%H:%M}: ${m.current_price:.2f} ({m.price_change_24h:+.2f}%)\n"

        return summary

    def _build_pattern_analysis_prompt(self, trades_summary: str, lookback_days: int) -> str:
        """Build prompt for pattern analysis"""

        return f"""Analyze the following trading history from the last {lookback_days} days and identify recurring patterns.

{trades_summary}

Please identify:

1. **Winning Patterns**: What characteristics do winning trades share?
   - Specific setups that work
   - Common indicators/conditions
   - Optimal leverage/position sizing
   - Time patterns (time of day, holding period)

2. **Losing Patterns**: What characteristics do losing trades share?
   - Setups that don't work
   - Common warning signs that were ignored
   - Mistakes in entry/exit

3. **Symbol-Specific Patterns**: Any patterns related to specific symbols?

4. **Emotional/Psychological Patterns**: Evidence of emotional trading?
   - Overconfidence after wins
   - Revenge trading after losses
   - FOMO entries

5. **Market Condition Patterns**: How does performance vary by market conditions?

For each pattern identified, provide:
- Pattern name/description
- How often it occurs
- Win rate when this pattern is present
- Actionable guidance (what to do when you see it)

Be specific and actionable. Focus on patterns that appear at least 3+ times."""

    def _parse_patterns_from_response(self, response_text: str, trades: List[TradeRecord]) -> List[Pattern]:
        """Parse patterns from LLM response"""

        patterns = []

        # Simple parsing - look for numbered patterns or bullet points
        # In production, you might ask LLM to return structured JSON

        sections = {
            'winning': 'Winning Pattern',
            'losing': 'Losing Pattern',
            'symbol_specific': 'Symbol-Specific Pattern',
            'emotional': 'Emotional Pattern',
            'market_condition': 'Market Condition Pattern'
        }

        current_type = 'general'
        pattern_buffer = []

        for line in response_text.split('\n'):
            line = line.strip()

            # Detect section changes
            for section_key, section_name in sections.items():
                if section_name.lower() in line.lower():
                    current_type = section_key
                    break

            # Detect pattern entries (look for patterns with indicators like bullet points, numbers, etc.)
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•') or line.startswith('*')):
                if pattern_buffer:
                    # Save previous pattern
                    pattern_text = ' '.join(pattern_buffer)
                    if len(pattern_text) > 20:  # Minimum length
                        patterns.append(Pattern(
                            pattern_type=current_type,
                            description=pattern_text[:500],  # Limit length
                            occurrences=self._count_occurrences(pattern_text, trades),
                            win_rate=0.0,  # Could be extracted from text
                            confidence=0.7,
                            discovered_at=int(datetime.now().timestamp() * 1000)
                        ))

                pattern_buffer = [line.lstrip('0123456789.-•*) ')]
            elif line and pattern_buffer:
                # Continue current pattern
                pattern_buffer.append(line)

        # Don't forget last pattern
        if pattern_buffer:
            pattern_text = ' '.join(pattern_buffer)
            if len(pattern_text) > 20:
                patterns.append(Pattern(
                    pattern_type=current_type,
                    description=pattern_text[:500],
                    occurrences=self._count_occurrences(pattern_text, trades),
                    win_rate=0.0,
                    confidence=0.7,
                    discovered_at=int(datetime.now().timestamp() * 1000)
                ))

        return patterns

    def _count_occurrences(self, pattern_text: str, trades: List[TradeRecord]) -> int:
        """Estimate how many times this pattern occurred (simple heuristic)"""

        # Simple keyword matching
        # In production, use more sophisticated matching

        keywords = pattern_text.lower().split()
        count = 0

        for trade in trades:
            trade_text = f"{trade.reasoning} {trade.close_reason or ''}".lower()
            matches = sum(1 for keyword in keywords if keyword in trade_text)

            # If several keywords match, count as occurrence
            if matches >= 2:
                count += 1

        return count


async def discover_trading_edges(
    database: TradingDatabase,
    ai_config: AIConfig,
    logger: Optional[logging.Logger] = None
) -> Dict[str, any]:
    """
    Use LLM to discover potential trading edges in historical data.

    This is a high-level function that runs multiple analyses:
    - Pattern recognition
    - Mistake identification
    - Strategy improvement suggestions
    - Market regime analysis

    Returns comprehensive insights dictionary.
    """

    recognizer = PatternRecognizer(ai_config, database, logger)

    logger.info("=" * 80)
    logger.info("🔬 Running Comprehensive Pattern Discovery")
    logger.info("=" * 80)

    # Analyze patterns
    patterns = await recognizer.analyze_trading_patterns(lookback_days=30)

    # Get recent trades
    cutoff = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
    all_trades = database.get_trades(from_timestamp=cutoff, status='closed')
    losses = [t for t in all_trades if (t.pnl or 0) < 0]

    # Identify mistakes
    mistakes = await recognizer.identify_trade_mistakes(losses) if losses else {}

    # Get current performance
    performance = database.get_latest_performance()
    perf_dict = performance.model_dump() if performance else {}

    # Get improvement suggestions
    suggestions = await recognizer.suggest_strategy_improvements(all_trades, perf_dict)

    logger.info("=" * 80)
    logger.info("📊 Discovery Complete")
    logger.info("=" * 80)

    return {
        "patterns": patterns,
        "common_mistakes": mistakes,
        "improvement_suggestions": suggestions,
        "trades_analyzed": len(all_trades),
        "timestamp": int(datetime.now().timestamp() * 1000)
    }
