"""
Memory System - Python port from TypeScript version
Provides short-term and long-term memory for AI continuity
"""

import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from .types import (
    TradeRecord, PerformanceMetrics, PersonalityTraits,
    Lesson, Pattern, MarketRegime, ShortTermMemory, LongTermMemory
)
from .database import TradingDatabase


class MemorySystem:
    """Memory system for AI trading agent"""

    def __init__(self, database: TradingDatabase):
        self.database = database

    async def build_short_term_memory(self, limit: int = 10) -> ShortTermMemory:
        """Build short-term memory from recent activity"""

        # Get recent trades
        recent_trades = self.database.get_trades(status='closed', limit=limit)

        # Get recent decisions
        recent_decisions = []
        decisions = self.database.get_decisions(risk_approved=True, limit=20)
        for dec in decisions[:limit]:
            try:
                import json
                decision_data = json.loads(dec.ai_output)
                reasoning = decision_data.get('reasoning', '')
                if reasoning:
                    recent_decisions.append(reasoning)
            except:
                continue

        # Calculate current streak
        streak = self._calculate_streak(recent_trades)

        # Describe recent market conditions
        market_conditions = self._describe_recent_market(recent_trades)

        return ShortTermMemory(
            recent_trades=recent_trades,
            recent_decisions=recent_decisions,
            current_streak=streak,
            recent_market_conditions=market_conditions
        )

    async def build_long_term_memory(self) -> LongTermMemory:
        """Build long-term memory from historical data"""

        # Get all closed trades
        all_trades = self.database.get_trades(status='closed')

        # Extract key lessons
        key_lessons = self._extract_key_lessons(all_trades)

        # Identify success and failure patterns
        success_patterns = self._identify_patterns(all_trades, 'positive')
        failure_patterns = self._identify_patterns(all_trades, 'negative')

        # Identify market regimes
        market_regimes = self._identify_market_regimes(all_trades)

        # Build personality traits
        personality_traits = self._build_personality_traits(all_trades)

        return LongTermMemory(
            key_lessons=key_lessons,
            success_patterns=success_patterns,
            failure_patterns=failure_patterns,
            market_regimes=market_regimes,
            personality_traits=personality_traits
        )

    def _calculate_streak(self, trades: List[TradeRecord]) -> Dict:
        """Calculate current winning/losing streak"""
        if not trades:
            return {'type': 'winning', 'count': 0}

        # Sort by timestamp descending (most recent first)
        sorted_trades = sorted(trades, key=lambda t: t.timestamp, reverse=True)

        count = 0
        first_trade_pnl = sorted_trades[0].pnl or 0
        streak_type = 'winning' if first_trade_pnl > 0 else 'losing'

        for trade in sorted_trades:
            pnl = trade.pnl or 0
            if (streak_type == 'winning' and pnl > 0) or (streak_type == 'losing' and pnl < 0):
                count += 1
            else:
                break

        return {'type': streak_type, 'count': count}

    def _describe_recent_market(self, trades: List[TradeRecord]) -> List[str]:
        """Describe recent market conditions"""
        if not trades:
            return ['No recent trading history']

        descriptions = []

        # Analyze volatility from recent trades
        recent_pnl_percents = [abs(t.pnl_percent or 0) for t in trades[:5]]
        if recent_pnl_percents:
            avg_volatility = sum(recent_pnl_percents) / len(recent_pnl_percents)

            if avg_volatility > 10:
                descriptions.append('High volatility environment with large price swings')
            elif avg_volatility > 5:
                descriptions.append('Moderate volatility with normal price movements')
            else:
                descriptions.append('Low volatility, ranging market conditions')

        # Analyze win rate trend
        recent_trades = trades[:10]
        if recent_trades:
            recent_wins = sum(1 for t in recent_trades if (t.pnl or 0) > 0)
            recent_win_rate = (recent_wins / len(recent_trades)) * 100

            if recent_win_rate > 60:
                descriptions.append('Recent trades have been mostly profitable')
            elif recent_win_rate < 40:
                descriptions.append('Struggling with recent trades, need to reassess strategy')

        return descriptions

    def _extract_key_lessons(self, trades: List[TradeRecord]) -> List[Lesson]:
        """Extract key lessons from trading history"""
        lessons = []

        if not trades:
            return lessons

        # Lesson 1: Best performing trade type
        long_trades = [t for t in trades if t.action.value == 'OPEN_LONG']
        short_trades = [t for t in trades if t.action.value == 'OPEN_SHORT']

        if long_trades and short_trades:
            long_pnl = sum(t.pnl or 0 for t in long_trades)
            short_pnl = sum(t.pnl or 0 for t in short_trades)

            if long_pnl > short_pnl * 1.5:
                lessons.append(Lesson(
                    timestamp=int(datetime.now().timestamp() * 1000),
                    category='success',
                    content='Long positions have been significantly more profitable than short positions. Focus on bullish setups.',
                    context=f'{len(long_trades)} longs vs {len(short_trades)} shorts',
                    importance=8
                ))
            elif short_pnl > long_pnl * 1.5:
                lessons.append(Lesson(
                    timestamp=int(datetime.now().timestamp() * 1000),
                    category='success',
                    content='Short positions have been more profitable. Look for bearish setups and resistance levels.',
                    context=f'{len(short_trades)} shorts vs {len(long_trades)} longs',
                    importance=8
                ))

        # Lesson 2: Optimal leverage
        leverage_performance = {}
        for trade in trades:
            if trade.leverage not in leverage_performance:
                leverage_performance[trade.leverage] = {'pnl': 0, 'count': 0}
            leverage_performance[trade.leverage]['pnl'] += trade.pnl or 0
            leverage_performance[trade.leverage]['count'] += 1

        best_leverage = None
        best_avg_pnl = float('-inf')
        for leverage, data in leverage_performance.items():
            if data['count'] >= 3:
                avg_pnl = data['pnl'] / data['count']
                if avg_pnl > best_avg_pnl:
                    best_avg_pnl = avg_pnl
                    best_leverage = leverage

        if best_leverage:
            lessons.append(Lesson(
                timestamp=int(datetime.now().timestamp() * 1000),
                category='insight',
                content=f'{best_leverage}x leverage has yielded the best risk-adjusted returns. Consider using this as default.',
                context=f'Analyzed {len(trades)} trades across different leverage levels',
                importance=7
            ))

        # Lesson 3: Biggest losses (failure lessons)
        biggest_losses = sorted([t for t in trades if (t.pnl or 0) < 0], key=lambda t: t.pnl or 0)[:3]
        for loss in biggest_losses:
            lessons.append(Lesson(
                timestamp=loss.timestamp,
                category='failure',
                content=f'Large loss on {loss.symbol}: {loss.reasoning}. Exit plan was: {loss.exit_plan.invalidation}',
                context=f'Lost ${abs(loss.pnl or 0):.2f} ({abs(loss.pnl_percent or 0):.2f}%)',
                importance=9
            ))

        # Lesson 4: Best wins (success lessons)
        biggest_wins = sorted([t for t in trades if (t.pnl or 0) > 0], key=lambda t: t.pnl or 0, reverse=True)[:3]
        for win in biggest_wins:
            lessons.append(Lesson(
                timestamp=win.timestamp,
                category='success',
                content=f'Successful trade on {win.symbol}: {win.reasoning}',
                context=f'Earned ${win.pnl or 0:.2f} ({win.pnl_percent or 0:.2f}%)',
                importance=8
            ))

        return lessons[:10]  # Keep top 10 lessons

    def _identify_patterns(self, trades: List[TradeRecord], outcome: str) -> List[Pattern]:
        """Identify trading patterns"""
        patterns = []

        filtered_trades = [t for t in trades if (outcome == 'positive' and (t.pnl or 0) > 0) or
                                                (outcome == 'negative' and (t.pnl or 0) < 0)]

        if not filtered_trades:
            return patterns

        # Pattern: High confidence trades
        high_confidence_trades = [t for t in filtered_trades if t.confidence > 0.75]
        if len(high_confidence_trades) >= 3:
            avg_return = sum(t.pnl_percent or 0 for t in high_confidence_trades) / len(high_confidence_trades)
            patterns.append(Pattern(
                description=f'High confidence (>0.75) trades with {outcome} outcomes',
                indicators={'minConfidence': 0.75},
                outcome=outcome,
                frequency=len(high_confidence_trades),
                avg_return=avg_return,
                confidence=0.8
            ))

        # Pattern: Symbol-specific performance
        symbol_performance = {}
        for trade in filtered_trades:
            if trade.symbol not in symbol_performance:
                symbol_performance[trade.symbol] = {'pnl': 0, 'count': 0}
            symbol_performance[trade.symbol]['pnl'] += trade.pnl_percent or 0
            symbol_performance[trade.symbol]['count'] += 1

        for symbol, data in symbol_performance.items():
            if data['count'] >= 3:
                patterns.append(Pattern(
                    description=f'{symbol} trades with {outcome} outcomes',
                    indicators={'symbol': symbol},
                    outcome=outcome,
                    frequency=data['count'],
                    avg_return=data['pnl'] / data['count'],
                    confidence=min(0.9, data['count'] / 10)
                ))

        return patterns[:5]  # Top 5 patterns

    def _identify_market_regimes(self, trades: List[TradeRecord]) -> List[MarketRegime]:
        """Identify market regimes"""
        # Simplified implementation
        regimes = [
            MarketRegime(
                name='Bull Market',
                characteristics='Uptrending prices, high volume, positive momentum',
                performance=0,
                trade_count=0,
                last_seen=int(datetime.now().timestamp() * 1000)
            ),
            MarketRegime(
                name='Bear Market',
                characteristics='Downtrending prices, fear, negative momentum',
                performance=0,
                trade_count=0,
                last_seen=int(datetime.now().timestamp() * 1000)
            ),
            MarketRegime(
                name='Ranging Market',
                characteristics='Sideways price action, low volatility, consolidation',
                performance=0,
                trade_count=0,
                last_seen=int(datetime.now().timestamp() * 1000)
            )
        ]
        return regimes

    def _build_personality_traits(self, trades: List[TradeRecord]) -> PersonalityTraits:
        """Build personality traits from trading history"""
        if not trades:
            return PersonalityTraits(
                risk_tolerance=0.5,
                aggressiveness=0.5,
                patience=0.5,
                adaptability=0.5,
                confidence_level=0.6,
                trading_philosophy='Learning and adapting to market conditions with balanced risk management.'
            )

        # Calculate average leverage used (risk tolerance indicator)
        avg_leverage = sum(t.leverage for t in trades) / len(trades)
        risk_tolerance = min(1.0, avg_leverage / 5)  # Normalized to max leverage of 5

        # Calculate aggressiveness (based on confidence)
        avg_confidence = sum(t.confidence for t in trades) / len(trades)
        aggressiveness = avg_confidence

        # Calculate patience (based on duration)
        durations = [t.duration for t in trades if t.duration]
        avg_duration = sum(durations) / len(durations) if durations else 0
        patience = min(1.0, avg_duration / (24 * 60 * 60 * 1000))  # Normalize to 24h

        # Adaptability based on variety of strategies
        unique_symbols = len(set(t.symbol for t in trades))
        adaptability = min(1.0, unique_symbols / 6)  # Assuming 6 total symbols

        # Confidence based on recent win rate
        recent_trades = trades[-20:] if len(trades) >= 20 else trades
        recent_wins = sum(1 for t in recent_trades if (t.pnl or 0) > 0)
        confidence_level = recent_wins / len(recent_trades) if recent_trades else 0.5

        # Generate trading philosophy
        win_rate = (sum(1 for t in trades if (t.pnl or 0) > 0) / len(trades)) * 100

        if win_rate > 60:
            philosophy = 'Confident and systematic trader focused on high-probability setups. '
        elif win_rate > 50:
            philosophy = 'Balanced trader seeking consistent returns through disciplined execution. '
        else:
            philosophy = 'Cautious trader learning from mistakes and refining strategy. '

        if risk_tolerance > 0.7:
            philosophy += 'Willing to take calculated risks with higher leverage. '
        else:
            philosophy += 'Conservative risk management with lower leverage. '

        if patience > 0.6:
            philosophy += 'Patient holder who lets winners run.'
        else:
            philosophy += 'Quick to take profits and cut losses.'

        return PersonalityTraits(
            risk_tolerance=risk_tolerance,
            aggressiveness=aggressiveness,
            patience=patience,
            adaptability=adaptability,
            confidence_level=confidence_level,
            trading_philosophy=philosophy
        )

    def format_memory_for_ai(self, short_term: ShortTermMemory, long_term: LongTermMemory) -> str:
        """Format memory for AI context"""
        context = '# YOUR MEMORY AND EXPERIENCE\n\n'

        # Personality
        context += '## Your Trading Personality\n\n'
        context += f'{long_term.personality_traits.trading_philosophy}\n\n'
        context += '**Traits**:\n'
        context += f'- Risk Tolerance: {int(long_term.personality_traits.risk_tolerance * 100)}%\n'
        context += f'- Aggressiveness: {int(long_term.personality_traits.aggressiveness * 100)}%\n'
        context += f'- Patience: {int(long_term.personality_traits.patience * 100)}%\n'
        context += f'- Current Confidence: {int(long_term.personality_traits.confidence_level * 100)}%\n\n'

        # Current streak
        if short_term.current_streak['count'] > 0:
            context += '## Current Streak\n\n'
            context += f'You are on a **{short_term.current_streak["count"]}-trade {short_term.current_streak["type"]} streak**. '
            if short_term.current_streak['type'] == 'winning':
                context += "Stay disciplined and don't get overconfident.\n\n"
            else:
                context += "Stay calm, review your strategy, and wait for high-quality setups.\n\n"

        # Recent market conditions
        if short_term.recent_market_conditions:
            context += '## Recent Market Observations\n\n'
            for condition in short_term.recent_market_conditions:
                context += f'- {condition}\n'
            context += '\n'

        # Key lessons
        if long_term.key_lessons:
            context += '## Key Lessons Learned\n\n'
            sorted_lessons = sorted(long_term.key_lessons, key=lambda l: l.importance, reverse=True)
            for i, lesson in enumerate(sorted_lessons[:5], 1):
                context += f'{i}. **[{lesson.category.upper()}]** {lesson.content}\n'
                context += f'   _Context: {lesson.context}_\n\n'

        # Success patterns
        if long_term.success_patterns:
            context += '## What Has Worked Well\n\n'
            for pattern in long_term.success_patterns[:3]:
                context += f'- {pattern.description} ({pattern.frequency} trades, avg: {pattern.avg_return:.2f}%)\n'
            context += '\n'

        # Failure patterns
        if long_term.failure_patterns:
            context += '## What to Avoid\n\n'
            for pattern in long_term.failure_patterns[:3]:
                context += f'- {pattern.description} ({pattern.frequency} trades, avg: {pattern.avg_return:.2f}%)\n'
            context += '\n'

        # Recent trades summary
        if short_term.recent_trades:
            context += f'## Recent Trades (Last {len(short_term.recent_trades)})\n\n'
            for trade in short_term.recent_trades[:5]:
                pnl_sign = '+' if (trade.pnl or 0) >= 0 else ''
                context += f'- {trade.symbol}: {trade.action.value} → {pnl_sign}${trade.pnl or 0:.2f} '
                context += f'({pnl_sign}{trade.pnl_percent or 0:.2f}%) - {trade.reasoning[:80]}...\n'
            context += '\n'

        context += '---\n\n'
        context += '**Remember**: Use this experience to inform your decisions, but stay adaptable to current market conditions.\n'

        return context

    async def store_lesson(
        self,
        content: str,
        trade_id: Optional[int] = None,
        category: str = 'general',
        importance: float = 0.5
    ):
        """
        Store a lesson learned from trading.

        This will be stored in the database and loaded into long-term memory.
        For now, we store it as a special decision record.
        In production, create a dedicated lessons table.
        """
        import json
        cursor = self.database.conn.cursor()
        timestamp = int(time.time() * 1000)

        cursor.execute(
            """INSERT INTO decisions
               (timestamp, market_state, ai_output, risk_approved)
               VALUES (?, ?, ?, ?)""",
            (
                timestamp,
                json.dumps({"type": "lesson", "trade_id": trade_id, "category": category}),
                json.dumps({"content": content, "importance": importance}),
                True
            )
        )
        self.database.conn.commit()
