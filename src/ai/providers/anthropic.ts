/**
 * Anthropic (Claude) AI Provider
 */

import Anthropic from '@anthropic-ai/sdk';
import type { IAIProvider, MarketState, TradingDecision, AIConfig } from '../../types/index.js';
import { AIProviderError } from '../../types/index.js';
import { z } from 'zod';

// Zod schema for validating AI response
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
});

export class AnthropicProvider implements IAIProvider {
  private client: Anthropic;
  private config: AIConfig;

  constructor(config: AIConfig) {
    this.config = config;
    this.client = new Anthropic({
      apiKey: config.apiKey,
    });
  }

  /**
   * Generate trading decision using Claude
   */
  async generateDecision(marketState: MarketState, systemPrompt: string): Promise<TradingDecision> {
    try {
      const userPrompt = this.buildUserPrompt(marketState);

      const response = await this.client.messages.create({
        model: this.config.model,
        max_tokens: this.config.maxTokens || 4000,
        temperature: this.config.temperature || 0.7,
        system: systemPrompt,
        messages: [
          {
            role: 'user',
            content: userPrompt,
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
   * Build user prompt with market data
   */
  private buildUserPrompt(marketState: MarketState): string {
    const { timestamp, pairs, account, performanceMetrics } = marketState;

    const date = new Date(timestamp).toISOString();

    let prompt = `# CURRENT MARKET STATE\n\n`;
    prompt += `**Time**: ${date}\n\n`;

    // Market data for each pair
    prompt += `## Market Data\n\n`;
    for (const [symbol, data] of Object.entries(pairs)) {
      prompt += `### ${symbol}\n`;
      prompt += `- **Price**: $${data.price.toFixed(2)}\n`;
      prompt += `- **24h Change**: ${data.priceChange24h.toFixed(2)}%\n`;
      prompt += `- **24h High/Low**: $${data.high24h.toFixed(2)} / $${data.low24h.toFixed(2)}\n`;
      prompt += `- **Volume 24h**: $${(data.volume24h / 1000000).toFixed(2)}M\n`;

      if (data.fundingRate !== undefined) {
        prompt += `- **Funding Rate**: ${(data.fundingRate * 100).toFixed(4)}%\n`;
      }

      // Technical indicators
      if (data.indicators) {
        prompt += `\n**Technical Indicators**:\n`;
        if (data.indicators.sma20) {
          prompt += `- SMA(20): $${data.indicators.sma20.toFixed(2)}\n`;
        }
        if (data.indicators.sma50) {
          prompt += `- SMA(50): $${data.indicators.sma50.toFixed(2)}\n`;
        }
        if (data.indicators.rsi) {
          prompt += `- RSI(14): ${data.indicators.rsi.toFixed(2)}\n`;
        }
        if (data.indicators.macd) {
          prompt += `- MACD: ${data.indicators.macd.macd.toFixed(2)} (signal: ${data.indicators.macd.signal.toFixed(2)})\n`;
        }
        if (data.indicators.bollingerBands) {
          const bb = data.indicators.bollingerBands;
          prompt += `- Bollinger Bands: $${bb.upper.toFixed(2)} / $${bb.middle.toFixed(2)} / $${bb.lower.toFixed(2)}\n`;
        }
      }

      prompt += `\n`;
    }

    // Account state
    prompt += `## Account State\n\n`;
    prompt += `- **Total Equity**: $${account.totalEquity.toFixed(2)}\n`;
    prompt += `- **Available Balance**: $${account.availableBalance.toFixed(2)}\n`;
    prompt += `- **Used Margin**: $${account.usedMargin.toFixed(2)}\n`;
    prompt += `- **Unrealized PnL**: $${account.unrealizedPnl.toFixed(2)}\n`;

    // Current positions
    if (account.positions.length > 0) {
      prompt += `\n**Current Positions**:\n`;
      for (const pos of account.positions) {
        prompt += `- ${pos.symbol}: ${pos.side.toUpperCase()} ${pos.size} contracts @ $${pos.entryPrice.toFixed(2)}, `;
        prompt += `Leverage: ${pos.leverage}x, PnL: $${pos.unrealizedPnl.toFixed(2)} (${pos.unrealizedPnlPercent.toFixed(2)}%)\n`;
      }
    } else {
      prompt += `\n**Current Positions**: None\n`;
    }

    // Performance metrics
    if (performanceMetrics) {
      prompt += `\n## Performance Metrics\n\n`;
      prompt += `- **Total PnL**: $${performanceMetrics.totalPnl.toFixed(2)} (${performanceMetrics.totalPnlPercent.toFixed(2)}%)\n`;
      prompt += `- **Sharpe Ratio**: ${performanceMetrics.sharpeRatio.toFixed(2)}\n`;
      prompt += `- **Win Rate**: ${performanceMetrics.winRate.toFixed(2)}%\n`;
      prompt += `- **Total Trades**: ${performanceMetrics.totalTrades}\n`;
      prompt += `- **Profit Factor**: ${performanceMetrics.profitFactor.toFixed(2)}\n`;
      prompt += `- **Max Drawdown**: ${performanceMetrics.maxDrawdownPercent.toFixed(2)}%\n`;
    }

    prompt += `\n---\n\n`;
    prompt += `Based on the above market data and your trading strategy, what is your next trading decision?\n`;
    prompt += `Please respond in the exact JSON format specified in the system prompt.`;

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
