/**
 * Post-Trade Analysis System
 * Analyzes completed trades to extract learnings and insights
 */

import type { TradeRecord, IDatabase, ILogger } from '../types/index.js';

export interface TradeAnalysis {
  tradeId: number;
  timestamp: number;
  outcome: 'success' | 'failure' | 'breakeven';
  analysis: string;
  keyTakeaways: string[];
  whatWorked: string[];
  whatDidntWork: string[];
  recommendations: string[];
  emotionalFactors?: string[];
}

export class PostTradeAnalyzer {
  constructor(
    private database: IDatabase,
    private logger: ILogger
  ) {}

  /**
   * Analyze a completed trade and extract learnings
   */
  async analyzeTrade(trade: TradeRecord): Promise<TradeAnalysis> {
    const pnl = trade.pnl || 0;
    const pnlPercent = trade.pnlPercent || 0;

    // Determine outcome
    let outcome: 'success' | 'failure' | 'breakeven';
    if (pnlPercent > 2) {
      outcome = 'success';
    } else if (pnlPercent < -2) {
      outcome = 'failure';
    } else {
      outcome = 'breakeven';
    }

    // Build analysis
    const analysis = this.buildAnalysisNarrative(trade, outcome, pnlPercent);

    // Extract key takeaways
    const keyTakeaways = this.extractKeyTakeaways(trade, outcome, pnlPercent);

    // Identify what worked
    const whatWorked = this.identifyWhatWorked(trade, outcome, pnlPercent);

    // Identify what didn't work
    const whatDidntWork = this.identifyWhatDidntWork(trade, outcome, pnlPercent);

    // Generate recommendations
    const recommendations = this.generateRecommendations(trade, outcome, pnlPercent);

    // Identify emotional factors (if any)
    const emotionalFactors = this.identifyEmotionalFactors(trade, outcome);

    const tradeAnalysis: TradeAnalysis = {
      tradeId: trade.id || 0,
      timestamp: Date.now(),
      outcome,
      analysis,
      keyTakeaways,
      whatWorked,
      whatDidntWork,
      recommendations,
      emotionalFactors,
    };

    this.logger.info('Post-trade analysis completed', {
      tradeId: trade.id,
      outcome,
      pnl: pnl.toFixed(2),
    });

    return tradeAnalysis;
  }

  /**
   * Build narrative analysis of the trade
   */
  private buildAnalysisNarrative(
    trade: TradeRecord,
    outcome: 'success' | 'failure' | 'breakeven',
    pnlPercent: number
  ): string {
    let narrative = '';

    // Opening context
    narrative += `Trade on ${trade.symbol} - ${trade.action} with ${trade.leverage}x leverage. `;
    narrative += `Entry: $${trade.entryPrice.toFixed(2)}, Exit: $${trade.exitPrice?.toFixed(2) || 'N/A'}. `;
    narrative += `Result: ${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}% (${pnlPercent >= 0 ? '+' : ''}$${(trade.pnl || 0).toFixed(2)}). `;

    // Outcome assessment
    if (outcome === 'success') {
      narrative += `This was a SUCCESSFUL trade. `;
      if (pnlPercent > 10) {
        narrative += `Exceptional performance! `;
      }
    } else if (outcome === 'failure') {
      narrative += `This was an UNSUCCESSFUL trade. `;
      if (pnlPercent < -5) {
        narrative += `Significant loss. `;
      }
    } else {
      narrative += `This trade resulted in minimal P&L. `;
    }

    // Duration analysis
    if (trade.duration) {
      const hours = trade.duration / (1000 * 60 * 60);
      narrative += `Held for ${hours.toFixed(1)} hours. `;

      if (hours < 1 && outcome === 'success') {
        narrative += `Quick profit capture was appropriate. `;
      } else if (hours > 24 && outcome === 'failure') {
        narrative += `Perhaps held too long hoping for recovery. `;
      }
    }

    // Confidence vs outcome
    if (trade.confidence > 0.75 && outcome === 'failure') {
      narrative += `Despite high confidence (${(trade.confidence * 100).toFixed(0)}%), the trade failed - review entry criteria. `;
    } else if (trade.confidence < 0.65 && outcome === 'success') {
      narrative += `Lower confidence (${(trade.confidence * 100).toFixed(0)}%) but still profitable - setup may be reliable. `;
    }

    // Exit analysis
    if (trade.closeReason) {
      narrative += `Closed because: ${trade.closeReason}. `;
    }

    // Original reasoning
    narrative += `Original thesis: "${trade.reasoning.substring(0, 150)}..."`;

    return narrative;
  }

  /**
   * Extract key takeaways from the trade
   */
  private extractKeyTakeaways(
    trade: TradeRecord,
    outcome: 'success' | 'failure' | 'breakeven',
    pnlPercent: number
  ): string[] {
    const takeaways: string[] = [];

    // Takeaway 1: Outcome context
    if (outcome === 'success') {
      if (pnlPercent > 10) {
        takeaways.push(`Excellent trade: +${pnlPercent.toFixed(2)}% validates the entry logic and patience`);
      } else {
        takeaways.push(`Profitable trade: The setup and execution were sound`);
      }
    } else if (outcome === 'failure') {
      if (Math.abs(pnlPercent) <= (trade.exitPlan.stopLoss * 1.1)) {
        takeaways.push(`Loss was within planned stop-loss - risk management worked as intended`);
      } else {
        takeaways.push(`Loss exceeded stop-loss plan - need stricter discipline on exits`);
      }
    }

    // Takeaway 2: Leverage usage
    if (trade.leverage >= 4) {
      if (outcome === 'success') {
        takeaways.push(`High leverage (${trade.leverage}x) amplified gains - use with caution`);
      } else if (outcome === 'failure') {
        takeaways.push(`High leverage (${trade.leverage}x) amplified losses - consider reducing leverage`);
      }
    } else if (trade.leverage <= 2) {
      takeaways.push(`Conservative leverage (${trade.leverage}x) kept risk manageable`);
    }

    // Takeaway 3: Confidence alignment
    if (trade.confidence > 0.8 && outcome === 'success') {
      takeaways.push(`High confidence was justified - this setup is reliable`);
    } else if (trade.confidence > 0.8 && outcome === 'failure') {
      takeaways.push(`High confidence doesn't guarantee success - stay humble`);
    } else if (trade.confidence < 0.65 && outcome === 'success') {
      takeaways.push(`Even moderate confidence trades can work - don't overthink`);
    }

    // Takeaway 4: Exit execution
    if (trade.closeReason?.includes('Take-profit')) {
      takeaways.push(`Exit plan executed perfectly - took profits at target`);
    } else if (trade.closeReason?.includes('Stop-loss')) {
      takeaways.push(`Stop-loss protected from larger losses - risk management is working`);
    }

    return takeaways;
  }

  /**
   * Identify what worked in this trade
   */
  private identifyWhatWorked(
    trade: TradeRecord,
    outcome: 'success' | 'failure' | 'breakeven',
    pnlPercent: number
  ): string[] {
    const worked: string[] = [];

    if (outcome === 'success') {
      // Entry timing
      worked.push(`Entry logic: ${trade.reasoning.split('.')[0]}`);

      // Position sizing
      worked.push(`Position sizing: ${trade.quantity} contracts with ${trade.leverage}x leverage`);

      // Exit plan
      if (trade.closeReason?.includes('Take-profit')) {
        worked.push(`Exit plan: Successfully hit take-profit target of ${trade.exitPlan.takeProfit}%`);
      }

      // Risk management
      if (trade.exitPlan.stopLoss) {
        worked.push(`Risk management: Stop-loss was set at ${trade.exitPlan.stopLoss}%`);
      }
    } else if (outcome === 'failure') {
      // Even in failure, some things might have worked
      if (Math.abs(pnlPercent) <= trade.exitPlan.stopLoss) {
        worked.push(`Risk management: Stop-loss prevented larger losses`);
      }

      if (trade.confidence < 0.7) {
        worked.push(`Appropriate caution: Lower confidence reflected uncertainty`);
      }
    }

    return worked;
  }

  /**
   * Identify what didn't work in this trade
   */
  private identifyWhatDidntWork(
    trade: TradeRecord,
    outcome: 'success' | 'failure' | 'breakeven',
    pnlPercent: number
  ): string[] {
    const didntWork: string[] = [];

    if (outcome === 'failure') {
      // Entry timing issues
      didntWork.push(`Entry logic was flawed: Market didn't move as expected`);

      // Direction was wrong
      if (trade.action === 'OPEN_LONG') {
        didntWork.push(`Bullish bias: ${trade.symbol} moved down instead of up`);
      } else if (trade.action === 'OPEN_SHORT') {
        didntWork.push(`Bearish bias: ${trade.symbol} moved up instead of down`);
      }

      // Stop-loss analysis
      if (Math.abs(pnlPercent) > trade.exitPlan.stopLoss * 1.2) {
        didntWork.push(`Exit discipline: Failed to honor stop-loss, resulting in larger loss`);
      }

      // Leverage too high
      if (trade.leverage >= 4) {
        didntWork.push(`Leverage too high: ${trade.leverage}x amplified losses unnecessarily`);
      }

      // High confidence but wrong
      if (trade.confidence > 0.75) {
        didntWork.push(`Overconfidence: ${(trade.confidence * 100).toFixed(0)}% confidence didn't translate to success`);
      }
    } else if (outcome === 'breakeven') {
      // Opportunity cost
      didntWork.push(`Trade didn't move significantly - may have been better opportunities`);

      // Exit too early?
      if (trade.duration && trade.duration < 1000 * 60 * 30) {
        didntWork.push(`Exited too quickly: May not have given trade enough time to develop`);
      }
    }

    return didntWork;
  }

  /**
   * Generate recommendations for future trades
   */
  private generateRecommendations(
    trade: TradeRecord,
    outcome: 'success' | 'failure' | 'breakeven',
    pnlPercent: number
  ): string[] {
    const recommendations: string[] = [];

    if (outcome === 'success') {
      // Reinforce successful patterns
      recommendations.push(`✓ This ${trade.symbol} setup worked well - look for similar patterns`);

      if (trade.confidence > 0.75) {
        recommendations.push(`✓ High-confidence setups on ${trade.symbol} are reliable`);
      }

      if (trade.leverage <= 3) {
        recommendations.push(`✓ Conservative leverage (${trade.leverage}x) provides good risk/reward`);
      }

      // Don't get complacent
      recommendations.push(`⚠ Don't assume all trades will work this well - maintain discipline`);

    } else if (outcome === 'failure') {
      // Correct the issues
      if (trade.confidence > 0.75) {
        recommendations.push(`! Be more critical when analyzing ${trade.symbol} - high confidence wasn't justified`);
      }

      if (trade.leverage >= 4) {
        recommendations.push(`! Reduce leverage to 2-3x on uncertain setups`);
      }

      if (Math.abs(pnlPercent) > trade.exitPlan.stopLoss) {
        recommendations.push(`! Must honor stop-loss levels - set alerts or use stop-loss orders`);
      }

      // Wait for better confirmation
      recommendations.push(`! Wait for stronger confirmation signals before entering ${trade.symbol}`);

      // Symbol-specific
      recommendations.push(`! Review historical performance on ${trade.symbol} - may not be your best instrument`);

    } else { // breakeven
      recommendations.push(`Consider being more selective - only trade when high conviction`);
      recommendations.push(`Evaluate if ${trade.symbol} is providing good opportunities vs alternatives`);
    }

    return recommendations;
  }

  /**
   * Identify emotional factors that may have influenced the trade
   */
  private identifyEmotionalFactors(
    trade: TradeRecord,
    outcome: 'success' | 'failure' | 'breakeven'
  ): string[] {
    const emotions: string[] = [];

    // Analyze based on patterns that suggest emotional trading

    // High leverage + high confidence might indicate overconfidence
    if (trade.leverage >= 4 && trade.confidence > 0.85) {
      emotions.push('Possible overconfidence: Very high leverage + very high confidence');
    }

    // Quick exit on losing trade might indicate fear
    if (outcome === 'failure' && trade.duration && trade.duration < 1000 * 60 * 30) {
      emotions.push('Possible panic exit: Closed losing position very quickly');
    }

    // Holding losing position too long might indicate hope/denial
    if (outcome === 'failure' && trade.duration && trade.duration > 1000 * 60 * 60 * 12) {
      emotions.push('Possible denial: Held losing position too long hoping for recovery');
    }

    // Low confidence but still traded might indicate FOMO
    if (trade.confidence < 0.65) {
      emotions.push('Possible FOMO: Took trade despite lower confidence');
    }

    return emotions;
  }

  /**
   * Perform batch analysis on recent trades to identify patterns
   */
  async analyzeTradingSession(
    fromTimestamp: number,
    toTimestamp: number
  ): Promise<string> {
    const trades = await this.database.getTrades({
      fromTimestamp,
      toTimestamp,
      status: 'closed',
    });

    if (trades.length === 0) {
      return 'No trades to analyze in this period.';
    }

    let report = `# Trading Session Analysis\n\n`;
    report += `Period: ${new Date(fromTimestamp).toISOString()} to ${new Date(toTimestamp).toISOString()}\n`;
    report += `Total Trades: ${trades.length}\n\n`;

    // Performance summary
    const totalPnl = trades.reduce((sum, t) => sum + (t.pnl || 0), 0);
    const winners = trades.filter(t => (t.pnl || 0) > 0);
    const losers = trades.filter(t => (t.pnl || 0) < 0);

    report += `## Session Performance\n`;
    report += `- Total P&L: $${totalPnl.toFixed(2)}\n`;
    report += `- Winners: ${winners.length} (${((winners.length / trades.length) * 100).toFixed(1)}%)\n`;
    report += `- Losers: ${losers.length} (${((losers.length / trades.length) * 100).toFixed(1)}%)\n`;
    report += `- Best Trade: $${Math.max(...trades.map(t => t.pnl || 0)).toFixed(2)}\n`;
    report += `- Worst Trade: $${Math.min(...trades.map(t => t.pnl || 0)).toFixed(2)}\n\n`;

    // Session insights
    report += `## Key Insights\n\n`;

    // Analyze by symbol
    const symbolStats = new Map<string, { pnl: number; count: number; wins: number }>();
    for (const trade of trades) {
      const current = symbolStats.get(trade.symbol) || { pnl: 0, count: 0, wins: 0 };
      current.pnl += trade.pnl || 0;
      current.count++;
      if ((trade.pnl || 0) > 0) current.wins++;
      symbolStats.set(trade.symbol, current);
    }

    report += `### By Symbol:\n`;
    symbolStats.forEach((stats, symbol) => {
      const winRate = (stats.wins / stats.count) * 100;
      report += `- ${symbol}: ${stats.count} trades, $${stats.pnl.toFixed(2)} P&L, ${winRate.toFixed(0)}% win rate\n`;
    });

    report += `\n### Session Recommendations:\n`;

    if (totalPnl > 0) {
      report += `- ✓ Profitable session - good work!\n`;
    } else {
      report += `- ⚠ Losing session - review what went wrong\n`;
    }

    if (winners.length / trades.length < 0.5) {
      report += `- ! Win rate below 50% - be more selective\n`;
    }

    return report;
  }
}
