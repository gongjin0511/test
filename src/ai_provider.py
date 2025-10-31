"""
AI Provider using Anthropic Claude
"""

import json
import re
from anthropic import Anthropic
from typing import Optional
from .types import TradingDecision, MarketState, AIConfig, AIProviderError, ExitPlan, TradingAction


class AnthropicProvider:
    """Anthropic Claude AI provider"""

    def __init__(self, config: AIConfig):
        self.config = config
        self.client = Anthropic(api_key=config.api_key)

    async def generate_decision(self, market_state: MarketState, system_prompt: str) -> TradingDecision:
        """Generate trading decision using Claude"""
        try:
            user_prompt = self._build_user_prompt(market_state)

            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            # Extract text content
            text_content = next(
                (block.text for block in response.content if hasattr(block, 'text')),
                None
            )

            if not text_content:
                raise AIProviderError("No text response from Claude")

            # Parse JSON response
            decision_data = self._parse_response(text_content)

            # Validate and create TradingDecision
            return TradingDecision(
                action=TradingAction(decision_data['action']),
                symbol=decision_data['symbol'],
                quantity=float(decision_data['quantity']),
                leverage=int(decision_data['leverage']),
                confidence=float(decision_data['confidence']),
                reasoning=decision_data['reasoning'],
                exit_plan=ExitPlan(**decision_data['exitPlan']),
                self_reflection=decision_data.get('selfReflection'),
                metadata={
                    'timestamp': market_state.timestamp,
                    'model_version': self.config.model,
                    'temperature': self.config.temperature
                }
            )

        except Exception as e:
            if isinstance(e, AIProviderError):
                raise
            raise AIProviderError(f"Failed to generate decision with Claude: {str(e)}")

    def _build_user_prompt(self, market_state: MarketState) -> str:
        """Build user prompt with market data"""
        prompt = "# CURRENT MARKET STATE\n\n"
        prompt += f"**Time**: {market_state.timestamp}\n\n"

        # Market data
        prompt += "## Market Data\n\n"
        for symbol, data in market_state.pairs.items():
            prompt += f"### {symbol}\n"
            prompt += f"- **Price**: ${data.price:.2f}\n"
            prompt += f"- **24h Change**: {data.price_change_24h:+.2f}%\n"
            prompt += f"- **Volume**: ${data.volume_24h/1e6:.2f}M\n"

            if data.indicators:
                prompt += "\n**Technical Indicators**:\n"
                if data.indicators.sma20:
                    prompt += f"- SMA(20): ${data.indicators.sma20:.2f}\n"
                if data.indicators.sma50:
                    prompt += f"- SMA(50): ${data.indicators.sma50:.2f}\n"
                if data.indicators.rsi:
                    prompt += f"- RSI(14): {data.indicators.rsi:.2f}\n"
                if data.indicators.macd:
                    prompt += f"- MACD: {data.indicators.macd['macd']:.2f}\n"

            prompt += "\n"

        # Account state
        prompt += "## Account State\n\n"
        prompt += f"- **Total Equity**: ${market_state.account.total_equity:.2f}\n"
        prompt += f"- **Available Balance**: ${market_state.account.available_balance:.2f}\n"
        prompt += f"- **Unrealized PnL**: ${market_state.account.unrealized_pnl:+.2f}\n\n"

        # Positions
        if market_state.account.positions:
            prompt += "### Current Positions\n\n"
            for pos in market_state.account.positions:
                prompt += f"- {pos.symbol}: {pos.side.value.upper()} {pos.size} @ ${pos.entry_price:.2f}\n"
                prompt += f"  PnL: ${pos.unrealized_pnl:+.2f} ({pos.unrealized_pnl_percent:+.2f}%)\n"
        else:
            prompt += "### Current Positions\nNone\n\n"

        prompt += "\n---\n\nWhat is your next trading decision?\n"

        return prompt

    def _parse_response(self, response_text: str) -> dict:
        """Parse JSON from AI response"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                raise AIProviderError("No JSON found in response")

            return json.loads(json_match.group(0))

        except json.JSONDecodeError as e:
            raise AIProviderError(f"Failed to parse JSON: {str(e)}", {"response": response_text})
