/**
 * Enhanced Anthropic (Claude) AI Provider with Memory and Learning
 */

import Anthropic from '@anthropic-ai/sdk';
import type { IAIProvider, MarketState, TradingDecision, AIConfig } from '../../types/index.js';
import { AIProviderError } from '../../types/index.js';
import { z } from 'zod';
import { MemorySystem } from '../../memory/memory-system.js';
import { DynamicPromptBuilder, selectPromptMode } from '../dynamic-prompt.js';
import type { IDatabase, ILogger } from '../../types/index.js';

const TradingDecisionSchema = z.object({
  action: z.enum(['OPEN_LONG', 'OPEN_SHORT', 'CLOSE', 'HOLD']),
  symbol: z.string(),
  quantity: z.number().positive(),
  leverage: z.number().min(1).max(125),
  confidence: z.number().min(0).max(1),
  reasoning: z.string().min(10),
  exitPlan: z.object({
    takeProfit: z.number().positive(),
    stopLoss: z.number().positive(),
    invalidation: z.string(),
  }),
  selfReflection: z.string().optional(), // New: AI's self-awareness
});

/**
 * Enhanced AI Provider with memory, learning, and self-awareness
 */
export class EnhancedAnthropicProvider implements IAIProvider {
  private client: Anthropic;
  private config: AIConfig;
  private memorySystem: MemorySystem;
  private promptBuilder: DynamicPromptBuilder;
  private logger: ILogger;

  constructor(
    config: AIConfig,
    database: IDatabase,
    logger: ILogger
  ) {
    this.config = config;
    this.client = new Anthropic({
      apiKey: config.apiKey,
    });
    this.memorySystem = new MemorySystem(database);
    this.promptBuilder = new DynamicPromptBuilder();
    this.logger = logger;
  }

  /**
   * Generate trading decision with full context and memory
   */
  async generateDecision(marketState: MarketState, baseSystemPrompt: string): Promise<TradingDecision> {
    try {
      // Step 1: Build memory context
      this.logger.debug('Building memory context...');
      const shortTermMemory = await this.memorySystem.buildShortTermMemory(10);
      const longTermMemory = await this.memorySystem.buildLongTermMemory();

      // Step 2: Select appropriate prompt mode based on performance
      const promptMode = selectPromptMode(marketState.performanceMetrics);
      this.logger.info('Prompt mode selected', { mode: promptMode });

      // Step 3: Build dynamic system prompt
      let systemPrompt = baseSystemPrompt;

      if (promptMode === 'crisis') {
        systemPrompt = this.promptBuilder.createCrisisPrompt() + '\n\n' + baseSystemPrompt;
      } else if (promptMode === 'fresh') {
        systemPrompt = this.promptBuilder.createFreshPerspectivePrompt() + '\n\n' + baseSystemPrompt;
      }

      // Add evolved personality and strategy adjustments
      systemPrompt = this.promptBuilder.buildEvolvingPrompt(
        systemPrompt,
        marketState.performanceMetrics,
        longTermMemory.personalityTraits
      );

      // Step 4: Add memory context to prompt
      const memoryContext = this.memorySystem.formatMemoryForAI(shortTermMemory, longTermMemory);
      systemPrompt = systemPrompt + '\n\n' + memoryContext;

      // Step 5: Build user prompt with market data
      const userPrompt = this.buildUserPrompt(marketState, shortTermMemory);

      // Step 6: Add self-reflection requirement
      const enhancedUserPrompt = userPrompt + `\n\n` +
        `**Additional Requirement**: After your decision, add a "selfReflection" field where you briefly reflect on:\n` +
        `- How does this decision align with your recent performance?\n` +
        `- Are you being influenced by recent wins/losses?\n` +
        `- What is your current emotional state (confident, cautious, uncertain)?\n` +
        `- Rate your discipline level (1-10) for this decision.\n`;

      this.logger.debug('Calling Claude with enhanced context', {
        systemPromptLength: systemPrompt.length,
        userPromptLength: enhancedUserPrompt.length,
        mode: promptMode,
      });

      // Step 7: Call Claude
      const response = await this.client.messages.create({
        model: this.config.model,
        max_tokens: this.config.maxTokens || 4000,
        temperature: this.config.temperature || 0.7,
        system: systemPrompt,
        messages: [
          {
            role: 'user',
            content: enhancedUserPrompt,
          },
        ],
      });

      // Extract text from response
      const textContent = response.content.find(block => block.type === 'text');
      if (!textContent || textContent.type !== 'text') {
        throw new AIProviderError('No text response from Claude');
      }

      // Parse JSON response
      const decision = this.parseResponse(textContent.text);

      // Log self-reflection if present
      if (decision.selfReflection) {
        this.logger.info('AI self-reflection', { reflection: decision.selfReflection });
      }

      return this.validateResponse(decision);
    } catch (error) {
      if (error instanceof AIProviderError) {
        throw error;
      }
      throw new AIProviderError(
        'Failed to generate decision with Claude',
        error instanceof Error ? error.message : 'Unknown error'
      );
    }
  }

  /**
   * Build user prompt with market data and memory cues
   */
  private buildUserPrompt(marketState: MarketState, shortTermMemory: any): string {
    const { timestamp, pairs, account, performanceMetrics } = marketState;

    const date = new Date(timestamp).toISOString();

    let prompt = `# CURRENT DECISION POINT\n\n`;
    prompt += `**Time**: ${date}\n`;
    prompt += `**Decision Number**: ${(performanceMetrics?.totalTrades || 0) + 1}\n\n`;

    // Add streak awareness
    if (shortTermMemory.currentStreak.count > 0) {
      const streakType = shortTermMemory.currentStreak.type;
      const count = shortTermMemory.currentStreak.count;
      if (streakType === 'winning') {
        prompt += `🔥 **Current Streak**: ${count} winning trades in a row. Stay disciplined, don't get overconfident.\n\n`;
      } else {
        prompt += `⚠️ **Current Streak**: ${count} losing trades. Stay calm, focus on process, wait for high-quality setups.\n\n`;
      }
    }

    // Market data for each pair
    prompt += `## Available Trading Opportunities\n\n`;
    for (const [symbol, data] of Object.entries(pairs)) {
      prompt += `### ${symbol}\n`;
      prompt += `- **Current Price**: $${data.price.toFixed(2)}\n`;
      prompt += `- **24h Change**: ${data.priceChange24h >= 0 ? '+' : ''}${data.priceChange24h.toFixed(2)}%\n`;
      prompt += `- **24h Range**: $${data.low24h.toFixed(2)} - $${data.high24h.toFixed(2)}\n`;
      prompt += `- **Volume**: $${(data.volume24h / 1000000).toFixed(2)}M\n`;

      if (data.fundingRate !== undefined) {
        prompt += `- **Funding Rate**: ${(data.fundingRate * 100).toFixed(4)}%\n`;
      }

      // Technical indicators with interpretation hints
      if (data.indicators) {
        prompt += `\n**Technical Setup**:\n`;

        // Price vs MA analysis
        if (data.indicators.sma20 && data.indicators.sma50) {
          const pricevsSMA20 = ((data.price - data.indicators.sma20) / data.indicators.sma20) * 100;
          const ma20vs50 = data.indicators.sma20 > data.indicators.sma50 ? 'bullish' : 'bearish';
          prompt += `- Price is ${pricevsSMA20.toFixed(2)}% ${pricevsSMA20 > 0 ? 'above' : 'below'} SMA(20)\n`;
          prompt += `- MA alignment: ${ma20vs50} (SMA20: $${data.indicators.sma20.toFixed(2)}, SMA50: $${data.indicators.sma50.toFixed(2)})\n`;
        }

        // RSI with zones
        if (data.indicators.rsi) {
          const rsi = data.indicators.rsi;
          let rsiZone = 'neutral';
          if (rsi > 70) rsiZone = 'overbought';
          else if (rsi < 30) rsiZone = 'oversold';
          else if (rsi > 60) rsiZone = 'bullish';
          else if (rsi < 40) rsiZone = 'bearish';

          prompt += `- RSI(14): ${rsi.toFixed(2)} [${rsiZone}]\n`;
        }

        // MACD
        if (data.indicators.macd) {
          const trend = data.indicators.macd.macd > data.indicators.macd.signal ? 'bullish' : 'bearish';
          prompt += `- MACD: ${trend} momentum (histogram: ${data.indicators.macd.histogram.toFixed(2)})\n`;
        }

        // Bollinger Bands
        if (data.indicators.bollingerBands) {
          const bb = data.indicators.bollingerBands;
          const position = data.price > bb.upper ? 'above upper' :
                          data.price < bb.lower ? 'below lower' : 'within';
          prompt += `- Bollinger Bands: Price ${position} (${bb.lower.toFixed(2)} - ${bb.upper.toFixed(2)})\n`;
        }

        // Volatility
        if (data.indicators.atr) {
          const atrPercent = (data.indicators.atr / data.price) * 100;
          prompt += `- Volatility (ATR): ${atrPercent.toFixed(2)}% ${atrPercent > 3 ? '[HIGH]' : atrPercent > 1.5 ? '[MODERATE]' : '[LOW]'}\n`;
        }
      }

      prompt += `\n`;
    }

    // Account state with context
    prompt += `## Your Current Account Status\n\n`;
    prompt += `- **Total Equity**: $${account.totalEquity.toFixed(2)}\n`;
    prompt += `- **Available to Trade**: $${account.availableBalance.toFixed(2)}\n`;
    prompt += `- **In Use (Margin)**: $${account.usedMargin.toFixed(2)}\n`;
    prompt += `- **Unrealized P&L**: ${account.unrealizedPnl >= 0 ? '+' : ''}$${account.unrealizedPnl.toFixed(2)}\n\n`;

    // Current positions with detailed status
    if (account.positions.length > 0) {
      prompt += `### Active Positions (${account.positions.length})\n\n`;
      for (const pos of account.positions) {
        const pnlSign = pos.unrealizedPnl >= 0 ? '+' : '';
        const emoji = pos.unrealizedPnl > 0 ? '✅' : '❌';
        prompt += `${emoji} **${pos.symbol}** - ${pos.side.toUpperCase()}\n`;
        prompt += `  - Size: ${pos.size} contracts @ $${pos.entryPrice.toFixed(2)}\n`;
        prompt += `  - Current: $${pos.currentPrice.toFixed(2)}\n`;
        prompt += `  - Leverage: ${pos.leverage}x\n`;
        prompt += `  - P&L: ${pnlSign}$${pos.unrealizedPnl.toFixed(2)} (${pnlSign}${pos.unrealizedPnlPercent.toFixed(2)}%)\n`;
        if (pos.liquidationPrice) {
          prompt += `  - Liquidation: $${pos.liquidationPrice.toFixed(2)}\n`;
        }
        prompt += `\n`;
      }
    } else {
      prompt += `### Active Positions\n\n`;
      prompt += `No open positions. You have full flexibility for new trades.\n\n`;
    }

    // Performance context with self-awareness prompts
    if (performanceMetrics) {
      prompt += `## Your Track Record\n\n`;
      prompt += `- **Total P&L**: ${performanceMetrics.totalPnl >= 0 ? '+' : ''}$${performanceMetrics.totalPnl.toFixed(2)} `;
      prompt += `(${performanceMetrics.totalPnlPercent >= 0 ? '+' : ''}${performanceMetrics.totalPnlPercent.toFixed(2)}%)\n`;
      prompt += `- **Sharpe Ratio**: ${performanceMetrics.sharpeRatio.toFixed(2)} ${performanceMetrics.sharpeRatio > 1 ? '✓' : performanceMetrics.sharpeRatio < 0.5 ? '⚠️' : ''}\n`;
      prompt += `- **Win Rate**: ${performanceMetrics.winRate.toFixed(1)}% (${performanceMetrics.winningTrades}W / ${performanceMetrics.losingTrades}L)\n`;
      prompt += `- **Profit Factor**: ${performanceMetrics.profitFactor === Infinity ? '∞' : performanceMetrics.profitFactor.toFixed(2)}\n`;
      prompt += `- **Max Drawdown**: ${performanceMetrics.maxDrawdownPercent.toFixed(2)}%\n`;
      prompt += `- **Today's P&L**: ${performanceMetrics.dailyPnl >= 0 ? '+' : ''}$${performanceMetrics.dailyPnl.toFixed(2)} `;
      prompt += `(${performanceMetrics.dailyPnlPercent >= 0 ? '+' : ''}${performanceMetrics.dailyPnlPercent.toFixed(2)}%)\n\n`;
    }

    prompt += `---\n\n`;
    prompt += `# WHAT IS YOUR NEXT MOVE?\n\n`;
    prompt += `Take a deep breath. Review the above information carefully.\n`;
    prompt += `Remember your lessons, stay true to your personality, but adapt to current conditions.\n\n`;
    prompt += `Respond with your decision in the exact JSON format specified in the system prompt.\n`;

    return prompt;
  }

  /**
   * Parse AI response text to extract JSON
   */
  private parseResponse(responseText: string): unknown {
    try {
      // Try to find JSON in the response
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new AIProviderError('No JSON found in response');
      }

      return JSON.parse(jsonMatch[0]);
    } catch (error) {
      throw new AIProviderError(
        'Failed to parse AI response',
        { responseText, error: error instanceof Error ? error.message : 'Unknown error' }
      );
    }
  }

  /**
   * Validate AI response against schema
   */
  validateResponse(response: unknown): TradingDecision {
    try {
      const validated = TradingDecisionSchema.parse(response);

      // Add metadata
      return {
        ...validated,
        metadata: {
          timestamp: Date.now(),
          modelVersion: this.config.model,
          temperature: this.config.temperature,
        },
      };
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new AIProviderError(
          'AI response validation failed',
          { errors: error.errors, response }
        );
      }
      throw error;
    }
  }
}
