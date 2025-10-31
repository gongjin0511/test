"""
Post-Trade Analysis System
Analyzes completed trades to extract learnings using AI
"""

from typing import List, Dict, Optional
from datetime import datetime
from .types import TradeRecord
from .database import TradingDatabase


class TradeAnalysis:
    """Trade analysis result"""
    def __init__(
        self,
        trade_id: int,
        timestamp: int,
        outcome: str,
        analysis: str,
        key_takeaways: List[str],
        what_worked: List[str],
        what_didnt_work: List[str],
        recommendations: List[str],
        emotional_factors: Optional[List[str]] = None
    ):
        self.trade_id = trade_id
        self.timestamp = timestamp
        self.outcome = outcome
        self.analysis = analysis
        self.key_takeaways = key_takeaways
        self.what_worked = what_worked
        self.what_didnt_work = what_didnt_work
        self.recommendations = recommendations
        self.emotional_factors = emotional_factors or []


class PostTradeAnalyzer:
    """Post-trade analysis system"""

    def __init__(self, database: TradingDatabase):
        self.database = database

    def analyze_trade(self, trade: TradeRecord) -> TradeAnalysis:
        """Analyze a completed trade"""
        pnl = trade.pnl or 0
        pnl_percent = trade.pnl_percent or 0

        # Determine outcome
        if pnl_percent > 2:
            outcome = 'success'
        elif pnl_percent < -2:
            outcome = 'failure'
        else:
            outcome = 'breakeven'

        # Build analysis
        analysis = self._build_analysis_narrative(trade, outcome, pnl_percent)

        # Extract key takeaways
        key_takeaways = self._extract_key_takeaways(trade, outcome, pnl_percent)

        # Identify what worked
        what_worked = self._identify_what_worked(trade, outcome, pnl_percent)

        # Identify what didn't work
        what_didnt_work = self._identify_what_didnt_work(trade, outcome, pnl_percent)

        # Generate recommendations
        recommendations = self._generate_recommendations(trade, outcome, pnl_percent)

        # Identify emotional factors
        emotional_factors = self._identify_emotional_factors(trade, outcome)

        return TradeAnalysis(
            trade_id=trade.id or 0,
            timestamp=int(datetime.now().timestamp() * 1000),
            outcome=outcome,
            analysis=analysis,
            key_takeaways=key_takeaways,
            what_worked=what_worked,
            what_didnt_work=what_didnt_work,
            recommendations=recommendations,
            emotional_factors=emotional_factors
        )

    def _build_analysis_narrative(self, trade: TradeRecord, outcome: str, pnl_percent: float) -> str:
        """Build narrative analysis of the trade"""
        narrative = f'Trade on {trade.symbol} - {trade.action.value} with {trade.leverage}x leverage. '
        narrative += f'Entry: ${trade.entry_price:.2f}, Exit: ${trade.exit_price or 0:.2f}. '
        narrative += f'Result: {pnl_percent:+.2f}% (${trade.pnl or 0:+.2f}). '

        if outcome == 'success':
            narrative += 'This was a SUCCESSFUL trade. '
            if pnl_percent > 10:
                narrative += 'Exceptional performance! '
        elif outcome == 'failure':
            narrative += 'This was an UNSUCCESSFUL trade. '
            if pnl_percent < -5:
                narrative += 'Significant loss. '
        else:
            narrative += 'This trade resulted in minimal P&L. '

        # Duration analysis
        if trade.duration:
            hours = trade.duration / (1000 * 60 * 60)
            narrative += f'Held for {hours:.1f} hours. '

        # Confidence vs outcome
        if trade.confidence > 0.75 and outcome == 'failure':
            narrative += f'Despite high confidence ({trade.confidence * 100:.0f}%), the trade failed - review entry criteria. '
        elif trade.confidence < 0.65 and outcome == 'success':
            narrative += f'Lower confidence ({trade.confidence * 100:.0f}%) but still profitable - setup may be reliable. '

        # Exit analysis
        if trade.close_reason:
            narrative += f'Closed because: {trade.close_reason}. '

        narrative += f'Original thesis: "{trade.reasoning[:150]}..."'

        return narrative

    def _extract_key_takeaways(self, trade: TradeRecord, outcome: str, pnl_percent: float) -> List[str]:
        """Extract key takeaways"""
        takeaways = []

        if outcome == 'success':
            if pnl_percent > 10:
                takeaways.append(f'Excellent trade: +{pnl_percent:.2f}% validates the entry logic and patience')
            else:
                takeaways.append('Profitable trade: The setup and execution were sound')
        elif outcome == 'failure':
            if abs(pnl_percent) <= (trade.exit_plan.stop_loss * 1.1):
                takeaways.append('Loss was within planned stop-loss - risk management worked as intended')
            else:
                takeaways.append('Loss exceeded stop-loss plan - need stricter discipline on exits')

        # Leverage usage
        if trade.leverage >= 4:
            if outcome == 'success':
                takeaways.append(f'High leverage ({trade.leverage}x) amplified gains - use with caution')
            else:
                takeaways.append(f'High leverage ({trade.leverage}x) amplified losses - consider reducing leverage')
        elif trade.leverage <= 2:
            takeaways.append(f'Conservative leverage ({trade.leverage}x) kept risk manageable')

        # Confidence alignment
        if trade.confidence > 0.8 and outcome == 'success':
            takeaways.append('High confidence was justified - this setup is reliable')
        elif trade.confidence > 0.8 and outcome == 'failure':
            takeaways.append("High confidence doesn't guarantee success - stay humble")

        return takeaways

    def _identify_what_worked(self, trade: TradeRecord, outcome: str, pnl_percent: float) -> List[str]:
        """Identify what worked"""
        worked = []

        if outcome == 'success':
            worked.append(f'Entry logic: {trade.reasoning.split(".")[0]}')
            worked.append(f'Position sizing: {trade.quantity} contracts with {trade.leverage}x leverage')

            if trade.close_reason and 'profit' in trade.close_reason.lower():
                worked.append(f'Exit plan: Successfully hit take-profit target of {trade.exit_plan.take_profit}%')

            if trade.exit_plan.stop_loss:
                worked.append(f'Risk management: Stop-loss was set at {trade.exit_plan.stop_loss}%')

        elif outcome == 'failure':
            if abs(pnl_percent) <= trade.exit_plan.stop_loss:
                worked.append('Risk management: Stop-loss prevented larger losses')

            if trade.confidence < 0.7:
                worked.append('Appropriate caution: Lower confidence reflected uncertainty')

        return worked

    def _identify_what_didnt_work(self, trade: TradeRecord, outcome: str, pnl_percent: float) -> List[str]:
        """Identify what didn't work"""
        didnt_work = []

        if outcome == 'failure':
            didnt_work.append('Entry logic was flawed: Market didn\'t move as expected')

            if trade.action.value == 'OPEN_LONG':
                didnt_work.append(f'Bullish bias: {trade.symbol} moved down instead of up')
            elif trade.action.value == 'OPEN_SHORT':
                didnt_work.append(f'Bearish bias: {trade.symbol} moved up instead of down')

            if abs(pnl_percent) > trade.exit_plan.stop_loss * 1.2:
                didnt_work.append('Exit discipline: Failed to honor stop-loss, resulting in larger loss')

            if trade.leverage >= 4:
                didnt_work.append(f'Leverage too high: {trade.leverage}x amplified losses unnecessarily')

            if trade.confidence > 0.75:
                didnt_work.append(f'Overconfidence: {trade.confidence * 100:.0f}% confidence didn\'t translate to success')

        elif outcome == 'breakeven':
            didnt_work.append('Trade didn\'t move significantly - may have been better opportunities')

            if trade.duration and trade.duration < 1000 * 60 * 30:
                didnt_work.append('Exited too quickly: May not have given trade enough time to develop')

        return didnt_work

    def _generate_recommendations(self, trade: TradeRecord, outcome: str, pnl_percent: float) -> List[str]:
        """Generate recommendations"""
        recommendations = []

        if outcome == 'success':
            recommendations.append(f'✓ This {trade.symbol} setup worked well - look for similar patterns')

            if trade.confidence > 0.75:
                recommendations.append(f'✓ High-confidence setups on {trade.symbol} are reliable')

            if trade.leverage <= 3:
                recommendations.append(f'✓ Conservative leverage ({trade.leverage}x) provides good risk/reward')

            recommendations.append('⚠ Don\'t assume all trades will work this well - maintain discipline')

        elif outcome == 'failure':
            if trade.confidence > 0.75:
                recommendations.append(f'! Be more critical when analyzing {trade.symbol} - high confidence wasn\'t justified')

            if trade.leverage >= 4:
                recommendations.append('! Reduce leverage to 2-3x on uncertain setups')

            if abs(pnl_percent) > trade.exit_plan.stop_loss:
                recommendations.append('! Must honor stop-loss levels - set alerts or use stop-loss orders')

            recommendations.append(f'! Wait for stronger confirmation signals before entering {trade.symbol}')
            recommendations.append(f'! Review historical performance on {trade.symbol} - may not be your best instrument')

        else:
            recommendations.append('Consider being more selective - only trade when high conviction')
            recommendations.append(f'Evaluate if {trade.symbol} is providing good opportunities vs alternatives')

        return recommendations

    def _identify_emotional_factors(self, trade: TradeRecord, outcome: str) -> List[str]:
        """Identify emotional factors"""
        emotions = []

        # High leverage + high confidence = overconfidence
        if trade.leverage >= 4 and trade.confidence > 0.85:
            emotions.append('Possible overconfidence: Very high leverage + very high confidence')

        # Quick exit on losing trade = panic
        if outcome == 'failure' and trade.duration and trade.duration < 1000 * 60 * 30:
            emotions.append('Possible panic exit: Closed losing position very quickly')

        # Holding losing position too long = denial
        if outcome == 'failure' and trade.duration and trade.duration > 1000 * 60 * 60 * 12:
            emotions.append('Possible denial: Held losing position too long hoping for recovery')

        # Low confidence but still traded = FOMO
        if trade.confidence < 0.65:
            emotions.append('Possible FOMO: Took trade despite lower confidence')

        return emotions

    def analyze_trading_session(self, from_timestamp: int, to_timestamp: int) -> str:
        """Analyze batch of trades in a session"""
        trades = self.database.get_trades(from_timestamp=from_timestamp, to_timestamp=to_timestamp, status='closed')

        if not trades:
            return 'No trades to analyze in this period.'

        report = '# Trading Session Analysis\n\n'
        report += f'Period: {datetime.fromtimestamp(from_timestamp/1000)} to {datetime.fromtimestamp(to_timestamp/1000)}\n'
        report += f'Total Trades: {len(trades)}\n\n'

        # Performance summary
        total_pnl = sum(t.pnl or 0 for t in trades)
        winners = [t for t in trades if (t.pnl or 0) > 0]
        losers = [t for t in trades if (t.pnl or 0) < 0]

        report += '## Session Performance\n'
        report += f'- Total P&L: ${total_pnl:.2f}\n'
        report += f'- Winners: {len(winners)} ({len(winners)/len(trades)*100:.1f}%)\n'
        report += f'- Losers: {len(losers)} ({len(losers)/len(trades)*100:.1f}%)\n'
        report += f'- Best Trade: ${max(t.pnl or 0 for t in trades):.2f}\n'
        report += f'- Worst Trade: ${min(t.pnl or 0 for t in trades):.2f}\n\n'

        # By symbol
        symbol_stats = {}
        for trade in trades:
            if trade.symbol not in symbol_stats:
                symbol_stats[trade.symbol] = {'pnl': 0, 'count': 0, 'wins': 0}
            symbol_stats[trade.symbol]['pnl'] += trade.pnl or 0
            symbol_stats[trade.symbol]['count'] += 1
            if (trade.pnl or 0) > 0:
                symbol_stats[trade.symbol]['wins'] += 1

        report += '### By Symbol:\n'
        for symbol, stats in symbol_stats.items():
            win_rate = (stats['wins'] / stats['count']) * 100
            report += f'- {symbol}: {stats["count"]} trades, ${stats["pnl"]:.2f} P&L, {win_rate:.0f}% win rate\n'

        report += '\n### Session Recommendations:\n'

        if total_pnl > 0:
            report += '- ✓ Profitable session - good work!\n'
        else:
            report += '- ⚠ Losing session - review what went wrong\n'

        if len(winners) / len(trades) < 0.5:
            report += '- ! Win rate below 50% - be more selective\n'

        return report
