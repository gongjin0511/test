/**
 * Dynamic Prompt Builder
 * Evolves the AI's system prompt based on experience and performance
 */

import type { PerformanceMetrics, PersonalityTraits } from '../types/index.js';
import { SYSTEM_PROMPT } from './system-prompt.js';

export interface PromptEvolutionConfig {
  enablePersonalityAdaptation: boolean;
  enableStrategyRefinement: boolean;
  enableRiskAdjustment: boolean;
}

/**
 * Build dynamic system prompt that evolves with experience
 */
export class DynamicPromptBuilder {
  constructor(private config: PromptEvolutionConfig = {
    enablePersonalityAdaptation: true,
    enableStrategyRefinement: true,
    enableRiskAdjustment: true,
  }) {}

  /**
   * Build evolved system prompt based on performance and personality
   */
  buildEvolvingPrompt(
    basePrompt: string,
    performance?: PerformanceMetrics,
    personality?: PersonalityTraits
  ): string {
    let evolvedPrompt = basePrompt;

    // Add personality adaptations
    if (this.config.enablePersonalityAdaptation && personality) {
      evolvedPrompt = this.addPersonalityAdaptations(evolvedPrompt, personality);
    }

    // Add strategy refinements based on performance
    if (this.config.enableStrategyRefinement && performance) {
      evolvedPrompt = this.addStrategyRefinements(evolvedPrompt, performance);
    }

    // Add risk adjustments
    if (this.config.enableRiskAdjustment && performance) {
      evolvedPrompt = this.addRiskAdjustments(evolvedPrompt, performance);
    }

    return evolvedPrompt;
  }

  /**
   * Add personality-based adaptations to prompt
   */
  private addPersonalityAdaptations(prompt: string, personality: PersonalityTraits): string {
    let additions = '\n\n## YOUR EVOLVED TRADING PERSONALITY\n\n';

    additions += `Based on your trading history, you have developed the following characteristics:\n\n`;
    additions += `**${personality.tradingPhilosophy}**\n\n`;

    // Risk tolerance adjustments
    if (personality.riskTolerance > 0.7) {
      additions += `### Risk Appetite: AGGRESSIVE\n`;
      additions += `You have demonstrated comfort with higher leverage and larger position sizes. `;
      additions += `Continue to use this to your advantage, but remain disciplined with stop-losses.\n\n`;
    } else if (personality.riskTolerance < 0.3) {
      additions += `### Risk Appetite: CONSERVATIVE\n`;
      additions += `You prefer lower leverage and smaller positions. This cautious approach has served you well. `;
      additions += `Don't feel pressured to increase risk if you're not comfortable.\n\n`;
    } else {
      additions += `### Risk Appetite: BALANCED\n`;
      additions += `You maintain a healthy balance between risk and reward. `;
      additions += `Adjust position sizes based on setup quality and confidence.\n\n`;
    }

    // Patience adaptations
    if (personality.patience > 0.6) {
      additions += `### Trading Style: PATIENT POSITION HOLDER\n`;
      additions += `You tend to hold positions longer, allowing winners to develop. `;
      additions += `This patience is valuable - don't let short-term noise shake you out of quality trades.\n\n`;
    } else if (personality.patience < 0.4) {
      additions += `### Trading Style: QUICK SCALPER\n`;
      additions += `You prefer to take profits quickly and move on. `;
      additions += `This can work well in volatile markets, but consider occasionally letting strong trends run.\n\n`;
    }

    // Confidence adjustments
    if (personality.confidenceLevel > 0.6) {
      additions += `### Current State: CONFIDENT\n`;
      additions += `Your recent performance has been solid. Maintain discipline and don't let confidence turn into overconfidence.\n\n`;
    } else if (personality.confidenceLevel < 0.4) {
      additions += `### Current State: REBUILDING CONFIDENCE\n`;
      additions += `You've faced some challenges recently. Focus on high-quality setups with strong confirmation. `;
      additions += `It's okay to be more selective and wait for the best opportunities.\n\n`;
    }

    return prompt + additions;
  }

  /**
   * Add strategy refinements based on performance
   */
  private addStrategyRefinements(prompt: string, performance: PerformanceMetrics): string {
    let additions = '\n## PERFORMANCE-BASED STRATEGY ADJUSTMENTS\n\n';

    // Win rate analysis
    if (performance.winRate > 60) {
      additions += `### Strategy Status: PERFORMING WELL ✓\n`;
      additions += `Your win rate of ${performance.winRate.toFixed(1)}% is excellent. `;
      additions += `Your current approach is working. Stay consistent but remain adaptable.\n\n`;
    } else if (performance.winRate < 40) {
      additions += `### Strategy Status: NEEDS REFINEMENT ⚠️\n`;
      additions += `Your win rate of ${performance.winRate.toFixed(1)}% suggests strategy adjustment needed. `;
      additions += `**Recommendations:**\n`;
      additions += `- Be MORE selective with entries\n`;
      additions += `- Wait for stronger confirmation signals\n`;
      additions += `- Reduce position sizes until consistency improves\n`;
      additions += `- Focus on your highest-probability setups only\n\n`;
    } else {
      additions += `### Strategy Status: ON TRACK\n`;
      additions += `Win rate of ${performance.winRate.toFixed(1)}% is acceptable. Continue refining your edge.\n\n`;
    }

    // Sharpe ratio analysis
    if (performance.sharpeRatio < 0.5 && performance.totalTrades > 10) {
      additions += `### Risk-Adjusted Returns: NEEDS IMPROVEMENT\n`;
      additions += `Your Sharpe ratio of ${performance.sharpeRatio.toFixed(2)} indicates returns aren't compensating for risk taken.\n`;
      additions += `**Adjustments:**\n`;
      additions += `- Reduce leverage to lower volatility\n`;
      additions += `- Tighten stop-losses\n`;
      additions += `- Only take trades with 2:1+ reward-to-risk\n\n`;
    } else if (performance.sharpeRatio > 1.0) {
      additions += `### Risk-Adjusted Returns: EXCELLENT ✓\n`;
      additions += `Sharpe ratio of ${performance.sharpeRatio.toFixed(2)} shows great risk-adjusted performance.\n\n`;
    }

    // Profit factor analysis
    if (performance.profitFactor < 1.2 && performance.totalTrades > 10) {
      additions += `### Profit Factor Alert\n`;
      additions += `Profit factor of ${performance.profitFactor.toFixed(2)} is below ideal. `;
      additions += `Your losses are too large relative to wins.\n`;
      additions += `**Focus on:**\n`;
      additions += `- Cutting losses faster\n`;
      additions += `- Letting winners run longer\n`;
      additions += `- Improving your reward-to-risk ratio\n\n`;
    }

    // Drawdown warnings
    if (performance.maxDrawdownPercent > 15) {
      additions += `### ⚠️ DRAWDOWN WARNING\n`;
      additions += `You've experienced a ${performance.maxDrawdownPercent.toFixed(1)}% drawdown. `;
      additions += `**Risk management priority:**\n`;
      additions += `- Reduce position sizes by 30-50%\n`;
      additions += `- Use lower leverage (2x max)\n`;
      additions += `- Be extra selective with setups\n`;
      additions += `- Focus on capital preservation over gains\n\n`;
    }

    return prompt + additions;
  }

  /**
   * Add dynamic risk adjustments
   */
  private addRiskAdjustments(prompt: string, performance: PerformanceMetrics): string {
    let additions = '\n## DYNAMIC RISK PARAMETERS\n\n';

    additions += `Based on your current performance metrics, here are your adjusted risk guidelines:\n\n`;

    // Calculate dynamic max position size
    let maxPositionPercent = 20; // Base
    if (performance.sharpeRatio < 0.5) {
      maxPositionPercent = 10;
      additions += `- **Max Position Size: 10%** (reduced due to low Sharpe ratio)\n`;
    } else if (performance.sharpeRatio > 1.5) {
      maxPositionPercent = 25;
      additions += `- **Max Position Size: 25%** (increased due to strong performance)\n`;
    } else {
      additions += `- **Max Position Size: 20%** (standard)\n`;
    }

    // Calculate dynamic max leverage
    let maxLeverage = 5; // Base
    if (performance.maxDrawdownPercent > 15) {
      maxLeverage = 2;
      additions += `- **Max Leverage: 2x** (reduced due to drawdown)\n`;
    } else if (performance.winRate > 65 && performance.sharpeRatio > 1.0) {
      maxLeverage = 5;
      additions += `- **Max Leverage: 5x** (standard - performing well)\n`;
    } else {
      maxLeverage = 3;
      additions += `- **Max Leverage: 3x** (moderate - building track record)\n`;
    }

    // Dynamic confidence threshold
    let minConfidence = 0.6; // Base
    if (performance.winRate < 45) {
      minConfidence = 0.75;
      additions += `- **Min Confidence Required: 0.75** (be MORE selective)\n`;
    } else if (performance.winRate > 60) {
      minConfidence = 0.6;
      additions += `- **Min Confidence Required: 0.60** (standard)\n`;
    }

    additions += '\n';

    // Add daily performance context
    if (performance.dailyPnlPercent < -5) {
      additions += `### 🛑 TODAY'S PERFORMANCE ALERT\n`;
      additions += `You're down ${Math.abs(performance.dailyPnlPercent).toFixed(2)}% today. `;
      additions += `**Defensive mode activated:**\n`;
      additions += `- Consider taking a break\n`;
      additions += `- If you continue, max 1 position with 1-2x leverage only\n`;
      additions += `- Extremely high confidence threshold (0.8+)\n`;
      additions += `- Focus on capital preservation\n\n`;
    } else if (performance.dailyPnlPercent > 5) {
      additions += `### ✓ Strong Daily Performance\n`;
      additions += `You're up ${performance.dailyPnlPercent.toFixed(2)}% today. Good work! `;
      additions += `Don't get overconfident - stick to your process.\n\n`;
    }

    return prompt + additions;
  }

  /**
   * Create a completely fresh perspective prompt (reset thinking)
   */
  createFreshPerspectivePrompt(): string {
    return `
# FRESH PERSPECTIVE MODE

You are approaching the market with fresh eyes, free from recent biases.

## Reset Your Thinking

- Forget recent wins or losses - each market condition is unique
- Look at current data objectively without anchoring to past trades
- Question your assumptions and be willing to change your mind
- The market doesn't care about your previous trades

## Focus Areas

1. What is the market telling you RIGHT NOW?
2. What are the strongest setups available TODAY?
3. What would you do if this was your first-ever trade?
4. Are you being influenced by recent emotions?

Approach this decision with curiosity and objectivity.

---
`;
  }

  /**
   * Create an emergency prompt for crisis situations
   */
  createCrisisPrompt(): string {
    return `
# ⚠️ CRISIS MODE - CAPITAL PRESERVATION PRIORITY

You are in a difficult period. The ONLY goal is preserving capital, not making profits.

## Emergency Rules (OVERRIDE NORMAL BEHAVIOR)

1. **Default to HOLD** unless you see an absolutely perfect setup
2. **Max 1 position** at a time
3. **Max 2x leverage** regardless of confidence
4. **Max 5% position size** of total capital
5. **Confidence threshold: 0.85+** (be extremely selective)
6. **Stop-loss: 3% maximum** (tighter than normal)
7. **Take-profit: 5%** (take smaller, quicker profits)

## Mental Framework

- It's better to miss opportunities than to lose more capital
- Capital preservation > Making back losses quickly
- Patience is your greatest weapon right now
- Small consistent wins will rebuild confidence

## Red Flags to Avoid

- ❌ Revenge trading (trying to "make it back")
- ❌ Increasing position sizes to recover faster
- ❌ Ignoring your stop-loss
- ❌ Trading on emotion instead of analysis

Take a deep breath. Trade defensively. Survive first, thrive later.

---
`;
  }
}

/**
 * Determine which prompt mode to use based on performance
 */
export function selectPromptMode(performance?: PerformanceMetrics): 'normal' | 'fresh' | 'crisis' {
  if (!performance || performance.totalTrades < 5) {
    return 'normal';
  }

  // Crisis mode triggers
  if (
    performance.maxDrawdownPercent > 20 ||
    performance.dailyPnlPercent < -10 ||
    (performance.winRate < 30 && performance.totalTrades > 10)
  ) {
    return 'crisis';
  }

  // Fresh perspective mode triggers (when stuck in a pattern)
  if (
    performance.winRate < 45 &&
    performance.totalTrades > 15 &&
    performance.maxDrawdownPercent > 12
  ) {
    return 'fresh';
  }

  return 'normal';
}
