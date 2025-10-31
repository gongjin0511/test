"""
Risk Management System
"""

from datetime import datetime
from .types import (
    TradingDecision, MarketState, RiskValidationResult,
    RiskConfig, TradingConfig, TradingAction
)


class RiskManager:
    """Risk management validator"""

    def __init__(self, risk_config: RiskConfig, trading_config: TradingConfig, initial_equity: float):
        self.risk_config = risk_config
        self.trading_config = trading_config
        self.start_of_day_equity = initial_equity
        self.daily_start_time = self._get_start_of_day()

    def validate_decision(
        self,
        decision: TradingDecision,
        market_state: MarketState
    ) -> RiskValidationResult:
        """Validate a trading decision against risk rules"""

        # HOLD is always approved
        if decision.action == TradingAction.HOLD:
            return RiskValidationResult(approved=True)

        checks = []

        # 1. Check confidence threshold
        checks.append(self._check_confidence(decision))

        # 2. Check position size
        checks.append(self._check_position_size(decision, market_state))

        # 3. Check leverage limits
        checks.append(self._check_leverage(decision))

        # 4. Check stop-loss requirements
        checks.append(self._check_stop_loss(decision))

        # 5. Check maximum positions
        checks.append(self._check_max_positions(decision, market_state))

        # 6. Check daily loss limit
        checks.append(self._check_daily_loss(market_state))

        # 7. Check portfolio exposure
        checks.append(self._check_portfolio_exposure(decision, market_state))

        # 8. Check short selling
        checks.append(self._check_short_selling(decision))

        # Collect failures
        failures = [c for c in checks if not c['passed']]

        if failures:
            reasons = '; '.join([f['reason'] for f in failures])
            return RiskValidationResult(
                approved=False,
                reason=reasons,
                warnings=[f['reason'] for f in failures]
            )

        return RiskValidationResult(approved=True)

    def _check_confidence(self, decision: TradingDecision) -> dict:
        """Check minimum confidence threshold"""
        if decision.confidence < self.risk_config.min_confidence_threshold:
            return {
                'passed': False,
                'reason': f"Confidence {decision.confidence:.2f} below threshold {self.risk_config.min_confidence_threshold}"
            }
        return {'passed': True}

    def _check_position_size(self, decision: TradingDecision, market_state: MarketState) -> dict:
        """Check position size limits"""
        if decision.action == TradingAction.CLOSE:
            return {'passed': True}

        market_price = market_state.pairs.get(decision.symbol)
        if not market_price:
            return {'passed': False, 'reason': f"No market price for {decision.symbol}"}

        position_value = decision.quantity * market_price.price
        position_percent = (position_value / market_state.account.total_equity) * 100

        if position_percent > self.trading_config.max_position_size_percent:
            return {
                'passed': False,
                'reason': f"Position size {position_percent:.2f}% exceeds maximum {self.trading_config.max_position_size_percent}%"
            }

        # Check sufficient balance
        required_margin = position_value / decision.leverage
        if required_margin > market_state.account.available_balance:
            return {
                'passed': False,
                'reason': f"Insufficient balance: Required ${required_margin:.2f}, Available ${market_state.account.available_balance:.2f}"
            }

        return {'passed': True}

    def _check_leverage(self, decision: TradingDecision) -> dict:
        """Check leverage limits"""
        if decision.leverage > self.trading_config.max_leverage:
            return {
                'passed': False,
                'reason': f"Leverage {decision.leverage}x exceeds maximum {self.trading_config.max_leverage}x"
            }
        if decision.leverage < 1:
            return {'passed': False, 'reason': "Leverage must be at least 1x"}

        return {'passed': True}

    def _check_stop_loss(self, decision: TradingDecision) -> dict:
        """Check stop-loss requirements"""
        if decision.action in [TradingAction.CLOSE, TradingAction.HOLD]:
            return {'passed': True}

        if self.risk_config.require_stop_loss and not decision.exit_plan.stop_loss:
            return {'passed': False, 'reason': "Stop-loss is required but not set"}

        if decision.exit_plan.stop_loss > self.trading_config.stop_loss_percent:
            return {
                'passed': False,
                'reason': f"Stop-loss {decision.exit_plan.stop_loss}% exceeds maximum {self.trading_config.stop_loss_percent}%"
            }

        return {'passed': True}

    def _check_max_positions(self, decision: TradingDecision, market_state: MarketState) -> dict:
        """Check maximum concurrent positions"""
        if decision.action in [TradingAction.CLOSE, TradingAction.HOLD]:
            return {'passed': True}

        current_positions = len(market_state.account.positions)

        if current_positions >= self.trading_config.max_concurrent_positions:
            return {
                'passed': False,
                'reason': f"Maximum concurrent positions ({self.trading_config.max_concurrent_positions}) reached"
            }

        return {'passed': True}

    def _check_daily_loss(self, market_state: MarketState) -> dict:
        """Check daily loss limit (circuit breaker)"""
        if not self.risk_config.circuit_breaker_enabled:
            return {'passed': True}

        current_equity = market_state.account.total_equity
        daily_loss = self.start_of_day_equity - current_equity
        daily_loss_percent = (daily_loss / self.start_of_day_equity) * 100

        if daily_loss_percent > self.risk_config.max_daily_loss_percent:
            return {
                'passed': False,
                'reason': f"Circuit breaker triggered: Daily loss {daily_loss_percent:.2f}% exceeds limit {self.risk_config.max_daily_loss_percent}%"
            }

        return {'passed': True}

    def _check_portfolio_exposure(self, decision: TradingDecision, market_state: MarketState) -> dict:
        """Check portfolio exposure limits"""
        if decision.action in [TradingAction.CLOSE, TradingAction.HOLD]:
            return {'passed': True}

        # Calculate current exposure
        current_exposure = sum(
            p.size * p.current_price
            for p in market_state.account.positions
        )

        # Calculate new position exposure
        market_price = market_state.pairs.get(decision.symbol)
        if not market_price:
            return {'passed': True}

        new_exposure = decision.quantity * market_price.price

        # Total exposure
        total_exposure = current_exposure + new_exposure
        exposure_percent = (total_exposure / market_state.account.total_equity) * 100

        if exposure_percent > self.risk_config.max_portfolio_exposure_percent:
            return {
                'passed': False,
                'reason': f"Total exposure {exposure_percent:.2f}% would exceed limit {self.risk_config.max_portfolio_exposure_percent}%"
            }

        return {'passed': True}

    def _check_short_selling(self, decision: TradingDecision) -> dict:
        """Check if short selling is allowed"""
        if not self.trading_config.enable_short_selling and decision.action == TradingAction.OPEN_SHORT:
            return {'passed': False, 'reason': "Short selling is disabled"}

        return {'passed': True}

    def _get_start_of_day(self) -> int:
        """Get start of current day timestamp"""
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(start_of_day.timestamp() * 1000)
