"""
Dynamic Prompt Builder
Evolves AI prompts based on performance and personality
"""

from typing import Optional
from .types import PerformanceMetrics, PersonalityTraits


class PromptEvolutionConfig:
    """Configuration for prompt evolution"""
    def __init__(
        self,
        enable_personality_adaptation: bool = True,
        enable_strategy_refinement: bool = True,
        enable_risk_adjustment: bool = True
    ):
        self.enable_personality_adaptation = enable_personality_adaptation
        self.enable_strategy_refinement = enable_strategy_refinement
        self.enable_risk_adjustment = enable_risk_adjustment


class DynamicPromptBuilder:
    """Builds dynamic system prompts that evolve with experience"""

    def __init__(self, config: Optional[PromptEvolutionConfig] = None):
        self.config = config or PromptEvolutionConfig()

    def build_evolving_prompt(
        self,
        base_prompt: str,
        performance: Optional[PerformanceMetrics] = None,
        personality: Optional[PersonalityTraits] = None
    ) -> str:
        """Build evolved system prompt"""
        evolved_prompt = base_prompt

        # Add personality adaptations
        if self.config.enable_personality_adaptation and personality:
            evolved_prompt = self._add_personality_adaptations(evolved_prompt, personality)

        # Add strategy refinements
        if self.config.enable_strategy_refinement and performance:
            evolved_prompt = self._add_strategy_refinements(evolved_prompt, performance)

        # Add risk adjustments
        if self.config.enable_risk_adjustment and performance:
            evolved_prompt = self._add_risk_adjustments(evolved_prompt, performance)

        return evolved_prompt

    def _add_personality_adaptations(self, prompt: str, personality: PersonalityTraits) -> str:
        """Add personality-based adaptations"""
        additions = '\n\n## YOUR EVOLVED TRADING PERSONALITY\n\n'
        additions += f'Based on your trading history, you have developed the following characteristics:\n\n'
        additions += f'**{personality.trading_philosophy}**\n\n'

        # Risk tolerance
        if personality.risk_tolerance > 0.7:
            additions += '### Risk Appetite: AGGRESSIVE\n'
            additions += 'You have demonstrated comfort with higher leverage and larger position sizes. '
            additions += 'Continue to use this to your advantage, but remain disciplined with stop-losses.\n\n'
        elif personality.risk_tolerance < 0.3:
            additions += '### Risk Appetite: CONSERVATIVE\n'
            additions += 'You prefer lower leverage and smaller positions. This cautious approach has served you well. '
            additions += 'Don\'t feel pressured to increase risk if you\'re not comfortable.\n\n'
        else:
            additions += '### Risk Appetite: BALANCED\n'
            additions += 'You maintain a healthy balance between risk and reward. '
            additions += 'Adjust position sizes based on setup quality and confidence.\n\n'

        # Patience
        if personality.patience > 0.6:
            additions += '### Trading Style: PATIENT POSITION HOLDER\n'
            additions += 'You tend to hold positions longer, allowing winners to develop. '
            additions += 'This patience is valuable - don\'t let short-term noise shake you out.\n\n'
        elif personality.patience < 0.4:
            additions += '### Trading Style: QUICK SCALPER\n'
            additions += 'You prefer to take profits quickly and move on. '
            additions += 'This can work well in volatile markets, but consider occasionally letting strong trends run.\n\n'

        # Confidence
        if personality.confidence_level > 0.6:
            additions += '### Current State: CONFIDENT\n'
            additions += 'Your recent performance has been solid. Maintain discipline and don\'t let confidence turn into overconfidence.\n\n'
        elif personality.confidence_level < 0.4:
            additions += '### Current State: REBUILDING CONFIDENCE\n'
            additions += 'You\'ve faced some challenges recently. Focus on high-quality setups with strong confirmation. '
            additions += 'It\'s okay to be more selective and wait for the best opportunities.\n\n'

        return prompt + additions

    def _add_strategy_refinements(self, prompt: str, performance: PerformanceMetrics) -> str:
        """Add strategy refinements based on performance"""
        additions = '\n## PERFORMANCE-BASED STRATEGY ADJUSTMENTS\n\n'

        # Win rate analysis
        if performance.win_rate > 60:
            additions += '### Strategy Status: PERFORMING WELL ✓\n'
            additions += f'Your win rate of {performance.win_rate:.1f}% is excellent. '
            additions += 'Your current approach is working. Stay consistent but remain adaptable.\n\n'
        elif performance.win_rate < 40:
            additions += '### Strategy Status: NEEDS REFINEMENT ⚠️\n'
            additions += f'Your win rate of {performance.win_rate:.1f}% suggests strategy adjustment needed. '
            additions += '**Recommendations:**\n'
            additions += '- Be MORE selective with entries\n'
            additions += '- Wait for stronger confirmation signals\n'
            additions += '- Reduce position sizes until consistency improves\n'
            additions += '- Focus on your highest-probability setups only\n\n'
        else:
            additions += '### Strategy Status: ON TRACK\n'
            additions += f'Win rate of {performance.win_rate:.1f}% is acceptable. Continue refining your edge.\n\n'

        # Sharpe ratio analysis
        if performance.sharpe_ratio < 0.5 and performance.total_trades > 10:
            additions += '### Risk-Adjusted Returns: NEEDS IMPROVEMENT\n'
            additions += f'Your Sharpe ratio of {performance.sharpe_ratio:.2f} indicates returns aren\'t compensating for risk taken.\n'
            additions += '**Adjustments:**\n'
            additions += '- Reduce leverage to lower volatility\n'
            additions += '- Tighten stop-losses\n'
            additions += '- Only take trades with 2:1+ reward-to-risk\n\n'
        elif performance.sharpe_ratio > 1.0:
            additions += '### Risk-Adjusted Returns: EXCELLENT ✓\n'
            additions += f'Sharpe ratio of {performance.sharpe_ratio:.2f} shows great risk-adjusted performance.\n\n'

        # Profit factor analysis
        if performance.profit_factor < 1.2 and performance.total_trades > 10:
            additions += '### Profit Factor Alert\n'
            additions += f'Profit factor of {performance.profit_factor:.2f} is below ideal. '
            additions += 'Your losses are too large relative to wins.\n'
            additions += '**Focus on:**\n'
            additions += '- Cutting losses faster\n'
            additions += '- Letting winners run longer\n'
            additions += '- Improving your reward-to-risk ratio\n\n'

        # Drawdown warnings
        if performance.max_drawdown_percent > 15:
            additions += '### ⚠️ DRAWDOWN WARNING\n'
            additions += f'You\'ve experienced a {performance.max_drawdown_percent:.1f}% drawdown. '
            additions += '**Risk management priority:**\n'
            additions += '- Reduce position sizes by 30-50%\n'
            additions += '- Use lower leverage (2x max)\n'
            additions += '- Be extra selective with setups\n'
            additions += '- Focus on capital preservation over gains\n\n'

        return prompt + additions

    def _add_risk_adjustments(self, prompt: str, performance: PerformanceMetrics) -> str:
        """Add dynamic risk adjustments"""
        additions = '\n## DYNAMIC RISK PARAMETERS\n\n'
        additions += 'Based on your current performance metrics, here are your adjusted risk guidelines:\n\n'

        # Dynamic max position size
        if performance.sharpe_ratio < 0.5:
            additions += '- **Max Position Size: 10%** (reduced due to low Sharpe ratio)\n'
        elif performance.sharpe_ratio > 1.5:
            additions += '- **Max Position Size: 25%** (increased due to strong performance)\n'
        else:
            additions += '- **Max Position Size: 20%** (standard)\n'

        # Dynamic max leverage
        if performance.max_drawdown_percent > 15:
            additions += '- **Max Leverage: 2x** (reduced due to drawdown)\n'
        elif performance.win_rate > 65 and performance.sharpe_ratio > 1.0:
            additions += '- **Max Leverage: 5x** (standard - performing well)\n'
        else:
            additions += '- **Max Leverage: 3x** (moderate - building track record)\n'

        # Dynamic confidence threshold
        if performance.win_rate < 45:
            additions += '- **Min Confidence Required: 0.75** (be MORE selective)\n'
        else:
            additions += '- **Min Confidence Required: 0.60** (standard)\n'

        additions += '\n'

        # Daily performance context
        if performance.daily_pnl_percent < -5:
            additions += '### 🛑 TODAY\'S PERFORMANCE ALERT\n'
            additions += f'You\'re down {abs(performance.daily_pnl_percent):.2f}% today. '
            additions += '**Defensive mode activated:**\n'
            additions += '- Consider taking a break\n'
            additions += '- If you continue, max 1 position with 1-2x leverage only\n'
            additions += '- Extremely high confidence threshold (0.8+)\n'
            additions += '- Focus on capital preservation\n\n'
        elif performance.daily_pnl_percent > 5:
            additions += '### ✓ Strong Daily Performance\n'
            additions += f'You\'re up {performance.daily_pnl_percent:.2f}% today. Good work! '
            additions += 'Don\'t get overconfident - stick to your process.\n\n'

        return prompt + additions

    def create_fresh_perspective_prompt(self) -> str:
        """Create a fresh perspective prompt (reset thinking)"""
        return '''
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
'''

    def create_crisis_prompt(self) -> str:
        """Create an emergency prompt for crisis situations"""
        return '''
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
'''


def select_prompt_mode(performance: Optional[PerformanceMetrics]) -> str:
    """Determine which prompt mode to use"""
    if not performance or performance.total_trades < 5:
        return 'normal'

    # Crisis mode triggers
    if (performance.max_drawdown_percent > 20 or
        performance.daily_pnl_percent < -10 or
        (performance.win_rate < 30 and performance.total_trades > 10)):
        return 'crisis'

    # Fresh perspective mode triggers
    if (performance.win_rate < 45 and
        performance.total_trades > 15 and
        performance.max_drawdown_percent > 12):
        return 'fresh'

    return 'normal'
