/**
 * Memory System for AI Trading Agent
 * Provides short-term and long-term memory to maintain continuity
 */

import type { IDatabase, TradeRecord, PerformanceMetrics, MarketSnapshot } from '../types/index.js';

export interface ShortTermMemory {
  recentTrades: TradeRecord[];           // Last N trades
  recentDecisions: string[];             // Last N decision reasonings
  currentStreak: {
    type: 'winning' | 'losing';
    count: number;
  };
  recentMarketConditions: string[];      // Description of recent market states
}

export interface LongTermMemory {
  keyLessons: Lesson[];                  // Important learnings
  successPatterns: Pattern[];            // Winning trade patterns
  failurePatterns: Pattern[];            // Losing trade patterns
  marketRegimes: MarketRegime[];         // Different market conditions experienced
  personalityTraits: PersonalityTraits;  // Evolved trading personality
}

export interface Lesson {
  id?: number;
  timestamp: number;
  category: 'success' | 'failure' | 'insight';
  content: string;                       // The lesson learned
  context: string;                       // Market conditions when learned
  importance: number;                    // 1-10 importance score
  applicationCount: number;              // How many times applied
}

export interface Pattern {
  id?: number;
  description: string;
  indicators: Record<string, any>;       // Technical conditions
  outcome: 'positive' | 'negative';
  frequency: number;
  avgReturn: number;
  confidence: number;
}

export interface MarketRegime {
  id?: number;
  name: string;                          // e.g., "High Volatility Bull", "Low Vol Bear"
  characteristics: string;
  performance: number;                   // How well we performed
  tradeCount: number;
  lastSeen: number;
}

export interface PersonalityTraits {
  riskTolerance: number;                 // 0-1, evolved from performance
  aggressiveness: number;                // 0-1, how quickly to enter trades
  patience: number;                      // 0-1, willingness to wait for setups
  adaptability: number;                  // 0-1, how quickly to change strategy
  confidenceLevel: number;               // 0-1, based on recent performance
  tradingPhilosophy: string;             // Evolved description of approach
}

export class MemorySystem {
  constructor(private database: IDatabase) {}

  /**
   * Build short-term memory from recent activity
   */
  async buildShortTermMemory(limit: number = 10): Promise<ShortTermMemory> {
    // Get recent trades
    const recentTrades = await this.database.getTrades({
      status: 'closed',
      limit,
    });

    // Get recent decisions (last 20)
    const recentDecisions = await this.database.getDecisions({ limit: 20 });
    const reasonings = recentDecisions
      .filter(d => d.riskApproved)
      .map(d => {
        try {
          const decision = JSON.parse(d.aiOutput);
          return decision.reasoning || '';
        } catch {
          return '';
        }
      })
      .filter(Boolean)
      .slice(0, limit);

    // Calculate current streak
    const streak = this.calculateStreak(recentTrades);

    // Describe recent market conditions
    const marketConditions = this.describeRecentMarket(recentTrades);

    return {
      recentTrades,
      recentDecisions: reasonings,
      currentStreak: streak,
      recentMarketConditions: marketConditions,
    };
  }

  /**
   * Build long-term memory from historical data
   */
  async buildLongTermMemory(): Promise<LongTermMemory> {
    // Get all closed trades for pattern analysis
    const allTrades = await this.database.getTrades({ status: 'closed' });

    // Extract key lessons
    const keyLessons = await this.extractKeyLessons(allTrades);

    // Identify success and failure patterns
    const successPatterns = await this.identifyPatterns(allTrades, 'positive');
    const failurePatterns = await this.identifyPatterns(allTrades, 'negative');

    // Identify market regimes
    const marketRegimes = await this.identifyMarketRegimes(allTrades);

    // Build personality traits based on trading history
    const personalityTraits = await this.buildPersonalityTraits(allTrades);

    return {
      keyLessons,
      successPatterns,
      failurePatterns,
      marketRegimes,
      personalityTraits,
    };
  }

  /**
   * Calculate current winning/losing streak
   */
  private calculateStreak(trades: TradeRecord[]): { type: 'winning' | 'losing'; count: number } {
    if (trades.length === 0) {
      return { type: 'winning', count: 0 };
    }

    // Sort by timestamp descending (most recent first)
    const sorted = [...trades].sort((a, b) => b.timestamp - a.timestamp);

    let count = 0;
    const firstTradePnl = sorted[0].pnl || 0;
    const type: 'winning' | 'losing' = firstTradePnl > 0 ? 'winning' : 'losing';

    for (const trade of sorted) {
      const pnl = trade.pnl || 0;
      if ((type === 'winning' && pnl > 0) || (type === 'losing' && pnl < 0)) {
        count++;
      } else {
        break;
      }
    }

    return { type, count };
  }

  /**
   * Describe recent market conditions
   */
  private describeRecentMarket(trades: TradeRecord[]): string[] {
    if (trades.length === 0) {
      return ['No recent trading history'];
    }

    const descriptions: string[] = [];

    // Analyze volatility from recent trades
    const recentPnlPercents = trades.slice(0, 5).map(t => Math.abs(t.pnlPercent || 0));
    const avgVolatility = recentPnlPercents.reduce((sum, v) => sum + v, 0) / recentPnlPercents.length;

    if (avgVolatility > 10) {
      descriptions.push('High volatility environment with large price swings');
    } else if (avgVolatility > 5) {
      descriptions.push('Moderate volatility with normal price movements');
    } else {
      descriptions.push('Low volatility, ranging market conditions');
    }

    // Analyze win rate trend
    const recentWins = trades.slice(0, 10).filter(t => (t.pnl || 0) > 0).length;
    const recentWinRate = (recentWins / Math.min(10, trades.length)) * 100;

    if (recentWinRate > 60) {
      descriptions.push('Recent trades have been mostly profitable');
    } else if (recentWinRate < 40) {
      descriptions.push('Struggling with recent trades, need to reassess strategy');
    }

    return descriptions;
  }

  /**
   * Extract key lessons from trading history
   */
  private async extractKeyLessons(trades: TradeRecord[]): Promise<Lesson[]> {
    const lessons: Lesson[] = [];

    if (trades.length === 0) {
      return lessons;
    }

    // Lesson 1: Best performing trade type
    const longTrades = trades.filter(t => t.action === 'OPEN_LONG');
    const shortTrades = trades.filter(t => t.action === 'OPEN_SHORT');

    const longPnl = longTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
    const shortPnl = shortTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);

    if (longTrades.length > 0 && shortTrades.length > 0) {
      if (longPnl > shortPnl * 1.5) {
        lessons.push({
          timestamp: Date.now(),
          category: 'success',
          content: 'Long positions have been significantly more profitable than short positions. Focus on bullish setups.',
          context: `${longTrades.length} longs vs ${shortTrades.length} shorts`,
          importance: 8,
          applicationCount: 0,
        });
      } else if (shortPnl > longPnl * 1.5) {
        lessons.push({
          timestamp: Date.now(),
          category: 'success',
          content: 'Short positions have been more profitable. Look for bearish setups and resistance levels.',
          context: `${shortTrades.length} shorts vs ${longTrades.length} longs`,
          importance: 8,
          applicationCount: 0,
        });
      }
    }

    // Lesson 2: Optimal leverage
    const leveragePerformance = new Map<number, { pnl: number; count: number }>();
    for (const trade of trades) {
      const current = leveragePerformance.get(trade.leverage) || { pnl: 0, count: 0 };
      current.pnl += trade.pnl || 0;
      current.count++;
      leveragePerformance.set(trade.leverage, current);
    }

    let bestLeverage = 1;
    let bestAvgPnl = -Infinity;
    leveragePerformance.forEach((data, leverage) => {
      const avgPnl = data.pnl / data.count;
      if (avgPnl > bestAvgPnl && data.count >= 3) {
        bestAvgPnl = avgPnl;
        bestLeverage = leverage;
      }
    });

    if (bestLeverage > 0) {
      lessons.push({
        timestamp: Date.now(),
        category: 'insight',
        content: `${bestLeverage}x leverage has yielded the best risk-adjusted returns. Consider using this as default.`,
        context: `Analyzed ${trades.length} trades across different leverage levels`,
        importance: 7,
        applicationCount: 0,
      });
    }

    // Lesson 3: Biggest losses (failure lessons)
    const biggestLosses = trades
      .filter(t => (t.pnl || 0) < 0)
      .sort((a, b) => (a.pnl || 0) - (b.pnl || 0))
      .slice(0, 3);

    for (const loss of biggestLosses) {
      lessons.push({
        timestamp: loss.timestamp,
        category: 'failure',
        content: `Large loss on ${loss.symbol}: ${loss.reasoning}. Exit plan was: ${loss.exitPlan.invalidation}`,
        context: `Lost $${Math.abs(loss.pnl || 0).toFixed(2)} (${Math.abs(loss.pnlPercent || 0).toFixed(2)}%)`,
        importance: 9,
        applicationCount: 0,
      });
    }

    // Lesson 4: Best wins (success lessons)
    const biggestWins = trades
      .filter(t => (t.pnl || 0) > 0)
      .sort((a, b) => (b.pnl || 0) - (a.pnl || 0))
      .slice(0, 3);

    for (const win of biggestWins) {
      lessons.push({
        timestamp: win.timestamp,
        category: 'success',
        content: `Successful trade on ${win.symbol}: ${win.reasoning}`,
        context: `Earned $${(win.pnl || 0).toFixed(2)} (${(win.pnlPercent || 0).toFixed(2)}%)`,
        importance: 8,
        applicationCount: 0,
      });
    }

    return lessons.slice(0, 10); // Keep top 10 lessons
  }

  /**
   * Identify trading patterns
   */
  private async identifyPatterns(
    trades: TradeRecord[],
    outcome: 'positive' | 'negative'
  ): Promise<Pattern[]> {
    const patterns: Pattern[] = [];

    const filteredTrades = trades.filter(t =>
      outcome === 'positive' ? (t.pnl || 0) > 0 : (t.pnl || 0) < 0
    );

    if (filteredTrades.length === 0) {
      return patterns;
    }

    // Pattern: High confidence trades
    const highConfidenceTrades = filteredTrades.filter(t => t.confidence > 0.75);
    if (highConfidenceTrades.length >= 3) {
      const avgReturn = highConfidenceTrades.reduce((sum, t) => sum + (t.pnlPercent || 0), 0) / highConfidenceTrades.length;
      patterns.push({
        description: `High confidence (>0.75) trades with ${outcome} outcomes`,
        indicators: { minConfidence: 0.75 },
        outcome,
        frequency: highConfidenceTrades.length,
        avgReturn,
        confidence: 0.8,
      });
    }

    // Pattern: Symbol-specific performance
    const symbolPerformance = new Map<string, { pnl: number; count: number }>();
    for (const trade of filteredTrades) {
      const current = symbolPerformance.get(trade.symbol) || { pnl: 0, count: 0 };
      current.pnl += trade.pnlPercent || 0;
      current.count++;
      symbolPerformance.set(trade.symbol, current);
    }

    symbolPerformance.forEach((data, symbol) => {
      if (data.count >= 3) {
        patterns.push({
          description: `${symbol} trades with ${outcome} outcomes`,
          indicators: { symbol },
          outcome,
          frequency: data.count,
          avgReturn: data.pnl / data.count,
          confidence: Math.min(0.9, data.count / 10),
        });
      }
    });

    return patterns.slice(0, 5); // Top 5 patterns
  }

  /**
   * Identify market regimes
   */
  private async identifyMarketRegimes(trades: TradeRecord[]): Promise<MarketRegime[]> {
    // Simplified market regime identification
    // In production, this would use clustering algorithms on market conditions

    const regimes: MarketRegime[] = [
      {
        name: 'Bull Market',
        characteristics: 'Uptrending prices, high volume, positive momentum',
        performance: 0,
        tradeCount: 0,
        lastSeen: Date.now(),
      },
      {
        name: 'Bear Market',
        characteristics: 'Downtrending prices, fear, negative momentum',
        performance: 0,
        tradeCount: 0,
        lastSeen: Date.now(),
      },
      {
        name: 'Ranging Market',
        characteristics: 'Sideways price action, low volatility, consolidation',
        performance: 0,
        tradeCount: 0,
        lastSeen: Date.now(),
      },
    ];

    return regimes;
  }

  /**
   * Build personality traits from trading history
   */
  private async buildPersonalityTraits(trades: TradeRecord[]): Promise<PersonalityTraits> {
    if (trades.length === 0) {
      // Default personality for new trader
      return {
        riskTolerance: 0.5,
        aggressiveness: 0.5,
        patience: 0.5,
        adaptability: 0.5,
        confidenceLevel: 0.6,
        tradingPhilosophy: 'Learning and adapting to market conditions with balanced risk management.',
      };
    }

    // Calculate average leverage used (risk tolerance indicator)
    const avgLeverage = trades.reduce((sum, t) => sum + t.leverage, 0) / trades.length;
    const riskTolerance = Math.min(1, avgLeverage / 5); // Normalized to max leverage of 5

    // Calculate aggressiveness (how quickly we enter trades - based on confidence)
    const avgConfidence = trades.reduce((sum, t) => sum + t.confidence, 0) / trades.length;
    const aggressiveness = avgConfidence;

    // Calculate patience (how long we hold positions)
    const avgDuration = trades.reduce((sum, t) => sum + (t.duration || 0), 0) / trades.length;
    const patience = Math.min(1, avgDuration / (24 * 60 * 60 * 1000)); // Normalize to 24h

    // Adaptability based on variety of strategies
    const uniqueSymbols = new Set(trades.map(t => t.symbol)).size;
    const adaptability = Math.min(1, uniqueSymbols / 6); // Assuming 6 total symbols

    // Confidence based on recent win rate
    const recentTrades = trades.slice(-20);
    const recentWins = recentTrades.filter(t => (t.pnl || 0) > 0).length;
    const confidenceLevel = recentWins / recentTrades.length;

    // Generate trading philosophy description
    const winRate = (trades.filter(t => (t.pnl || 0) > 0).length / trades.length) * 100;
    let philosophy = '';

    if (winRate > 60) {
      philosophy = 'Confident and systematic trader focused on high-probability setups. ';
    } else if (winRate > 50) {
      philosophy = 'Balanced trader seeking consistent returns through disciplined execution. ';
    } else {
      philosophy = 'Cautious trader learning from mistakes and refining strategy. ';
    }

    if (riskTolerance > 0.7) {
      philosophy += 'Willing to take calculated risks with higher leverage. ';
    } else {
      philosophy += 'Conservative risk management with lower leverage. ';
    }

    if (patience > 0.6) {
      philosophy += 'Patient holder who lets winners run.';
    } else {
      philosophy += 'Quick to take profits and cut losses.';
    }

    return {
      riskTolerance,
      aggressiveness,
      patience,
      adaptability,
      confidenceLevel,
      tradingPhilosophy: philosophy,
    };
  }

  /**
   * Format memory for AI context
   */
  formatMemoryForAI(shortTerm: ShortTermMemory, longTerm: LongTermMemory): string {
    let context = '# YOUR MEMORY AND EXPERIENCE\n\n';

    // Personality
    context += '## Your Trading Personality\n\n';
    context += `${longTerm.personalityTraits.tradingPhilosophy}\n\n`;
    context += `**Traits**:\n`;
    context += `- Risk Tolerance: ${(longTerm.personalityTraits.riskTolerance * 100).toFixed(0)}%\n`;
    context += `- Aggressiveness: ${(longTerm.personalityTraits.aggressiveness * 100).toFixed(0)}%\n`;
    context += `- Patience: ${(longTerm.personalityTraits.patience * 100).toFixed(0)}%\n`;
    context += `- Current Confidence: ${(longTerm.personalityTraits.confidenceLevel * 100).toFixed(0)}%\n\n`;

    // Current streak
    if (shortTerm.currentStreak.count > 0) {
      context += `## Current Streak\n\n`;
      context += `You are on a **${shortTerm.currentStreak.count}-trade ${shortTerm.currentStreak.type} streak**. `;
      if (shortTerm.currentStreak.type === 'winning') {
        context += 'Stay disciplined and don\'t get overconfident.\n\n';
      } else {
        context += 'Stay calm, review your strategy, and wait for high-quality setups.\n\n';
      }
    }

    // Recent market conditions
    if (shortTerm.recentMarketConditions.length > 0) {
      context += `## Recent Market Observations\n\n`;
      shortTerm.recentMarketConditions.forEach(condition => {
        context += `- ${condition}\n`;
      });
      context += '\n';
    }

    // Key lessons
    if (longTerm.keyLessons.length > 0) {
      context += `## Key Lessons Learned\n\n`;
      longTerm.keyLessons
        .sort((a, b) => b.importance - a.importance)
        .slice(0, 5)
        .forEach((lesson, i) => {
          context += `${i + 1}. **[${lesson.category.toUpperCase()}]** ${lesson.content}\n`;
          context += `   _Context: ${lesson.context}_\n\n`;
        });
    }

    // Success patterns
    if (longTerm.successPatterns.length > 0) {
      context += `## What Has Worked Well\n\n`;
      longTerm.successPatterns.slice(0, 3).forEach(pattern => {
        context += `- ${pattern.description} (${pattern.frequency} trades, avg: ${pattern.avgReturn.toFixed(2)}%)\n`;
      });
      context += '\n';
    }

    // Failure patterns
    if (longTerm.failurePatterns.length > 0) {
      context += `## What to Avoid\n\n`;
      longTerm.failurePatterns.slice(0, 3).forEach(pattern => {
        context += `- ${pattern.description} (${pattern.frequency} trades, avg: ${pattern.avgReturn.toFixed(2)}%)\n`;
      });
      context += '\n';
    }

    // Recent trades summary
    if (shortTerm.recentTrades.length > 0) {
      context += `## Recent Trades (Last ${shortTerm.recentTrades.length})\n\n`;
      shortTerm.recentTrades.slice(0, 5).forEach(trade => {
        const pnlSign = (trade.pnl || 0) >= 0 ? '+' : '';
        context += `- ${trade.symbol}: ${trade.action} → ${pnlSign}$${(trade.pnl || 0).toFixed(2)} `;
        context += `(${pnlSign}${(trade.pnlPercent || 0).toFixed(2)}%) - ${trade.reasoning.substring(0, 80)}...\n`;
      });
      context += '\n';
    }

    context += '---\n\n';
    context += '**Remember**: Use this experience to inform your decisions, but stay adaptable to current market conditions.\n';

    return context;
  }
}
