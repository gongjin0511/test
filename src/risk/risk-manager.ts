/**
 * Risk Management System
 * Validates trading decisions against risk parameters
 */

import type {
  IRiskManager,
  TradingDecision,
  MarketState,
  RiskValidationResult,
  RiskMetrics,
  RiskConfig,
  TradingConfig,
} from '../types/index.js';
import type { ILogger } from '../types/index.js';

export class RiskManager implements IRiskManager {
  private riskConfig: RiskConfig;
  private tradingConfig: TradingConfig;
  private logger: ILogger;
  private startOfDayEquity: number;
  private dailyStartTime: number;

  constructor(
    riskConfig: RiskConfig,
    tradingConfig: TradingConfig,
    logger: ILogger,
    initialEquity: number
  ) {
    this.riskConfig = riskConfig;
    this.tradingConfig = tradingConfig;
    this.logger = logger;
    this.startOfDayEquity = initialEquity;
    this.dailyStartTime = this.getStartOfDay();
  }

  /**
   * Validate a trading decision against risk rules
   */
  validateDecision(decision: TradingDecision, marketState: MarketState): RiskValidationResult {
    const checks: { passed: boolean; reason?: string }[] = [];

    // 1. Check if it's a HOLD decision (always approved)
    if (decision.action === 'HOLD') {
      return { approved: true };
    }

    // 2. Check confidence threshold
    const confidenceCheck = this.checkConfidence(decision);
    checks.push(confidenceCheck);

    // 3. Check position size
    const positionSizeCheck = this.checkPositionSize(decision, marketState);
    checks.push(positionSizeCheck);

    // 4. Check leverage limits
    const leverageCheck = this.checkLeverage(decision);
    checks.push(leverageCheck);

    // 5. Check stop-loss requirements
    const stopLossCheck = this.checkStopLoss(decision);
    checks.push(stopLossCheck);

    // 6. Check maximum concurrent positions
    const maxPositionsCheck = this.checkMaxPositions(decision, marketState);
    checks.push(maxPositionsCheck);

    // 7. Check daily loss limit (circuit breaker)
    const dailyLossCheck = this.checkDailyLoss(marketState);
    checks.push(dailyLossCheck);

    // 8. Check portfolio exposure
    const exposureCheck = this.checkPortfolioExposure(decision, marketState);
    checks.push(exposureCheck);

    // 9. Check if short selling is allowed
    const shortSellingCheck = this.checkShortSelling(decision);
    checks.push(shortSellingCheck);

    // Collect all failures
    const failures = checks.filter(c => !c.passed);

    if (failures.length > 0) {
      const reasons = failures.map(f => f.reason).join('; ');
      this.logger.warn('Trading decision rejected', { decision, reasons });

      return {
        approved: false,
        reason: reasons,
        warnings: failures.map(f => f.reason || 'Unknown risk violation'),
      };
    }

    this.logger.info('Trading decision approved', { decision });

    return { approved: true };
  }

  /**
   * Check if circuit breaker should be triggered
   */
  checkCircuitBreaker(): boolean {
    // Circuit breaker is checked in checkDailyLoss
    return false; // Placeholder
  }

  /**
   * Update risk metrics based on current market state
   */
  updateRiskMetrics(marketState: MarketState): RiskMetrics {
    const { account } = marketState;

    // Calculate total exposure
    const currentExposure = account.positions.reduce(
      (sum, pos) => sum + (pos.size * pos.currentPrice),
      0
    );

    const exposurePercent = (currentExposure / account.totalEquity) * 100;

    // Calculate portfolio leverage
    const portfolioLeverage = account.positions.reduce(
      (sum, pos) => sum + pos.leverage * (pos.size * pos.currentPrice / account.totalEquity),
      0
    );

    // Max single position size
    const maxSinglePositionSize = Math.max(
      0,
      ...account.positions.map(pos => pos.size * pos.currentPrice)
    );

    // Available risk capital
    const availableRiskCapital = account.availableBalance;

    const metrics: RiskMetrics = {
      currentExposure,
      exposurePercent,
      maxSinglePositionSize,
      portfolioLeverage,
      availableRiskCapital,
    };

    // Reset daily tracking if new day
    if (Date.now() - this.dailyStartTime > 24 * 60 * 60 * 1000) {
      this.startOfDayEquity = account.totalEquity;
      this.dailyStartTime = this.getStartOfDay();
    }

    return metrics;
  }

  /**
   * Check minimum confidence threshold
   */
  private checkConfidence(decision: TradingDecision): { passed: boolean; reason?: string } {
    if (decision.confidence < this.riskConfig.minConfidenceThreshold) {
      return {
        passed: false,
        reason: `Confidence ${decision.confidence.toFixed(2)} below minimum threshold ${this.riskConfig.minConfidenceThreshold}`,
      };
    }
    return { passed: true };
  }

  /**
   * Check position size limits
   */
  private checkPositionSize(
    decision: TradingDecision,
    marketState: MarketState
  ): { passed: boolean; reason?: string } {
    if (decision.action === 'CLOSE') {
      return { passed: true };
    }

    const { account } = marketState;
    const marketPrice = marketState.pairs[decision.symbol]?.price || 0;
    const positionValue = decision.quantity * marketPrice;
    const positionPercent = (positionValue / account.totalEquity) * 100;

    if (positionPercent > this.tradingConfig.maxPositionSizePercent) {
      return {
        passed: false,
        reason: `Position size ${positionPercent.toFixed(2)}% exceeds maximum ${this.tradingConfig.maxPositionSizePercent}%`,
      };
    }

    // Check if sufficient balance
    const requiredMargin = positionValue / decision.leverage;
    if (requiredMargin > account.availableBalance) {
      return {
        passed: false,
        reason: `Insufficient balance: Required $${requiredMargin.toFixed(2)}, Available $${account.availableBalance.toFixed(2)}`,
      };
    }

    return { passed: true };
  }

  /**
   * Check leverage limits
   */
  private checkLeverage(decision: TradingDecision): { passed: boolean; reason?: string } {
    if (decision.leverage > this.tradingConfig.maxLeverage) {
      return {
        passed: false,
        reason: `Leverage ${decision.leverage}x exceeds maximum ${this.tradingConfig.maxLeverage}x`,
      };
    }

    if (decision.leverage < 1) {
      return {
        passed: false,
        reason: `Leverage must be at least 1x`,
      };
    }

    return { passed: true };
  }

  /**
   * Check stop-loss requirements
   */
  private checkStopLoss(decision: TradingDecision): { passed: boolean; reason?: string } {
    if (decision.action === 'CLOSE' || decision.action === 'HOLD') {
      return { passed: true };
    }

    if (this.riskConfig.requireStopLoss && !decision.exitPlan.stopLoss) {
      return {
        passed: false,
        reason: 'Stop-loss is required but not set',
      };
    }

    if (decision.exitPlan.stopLoss > this.tradingConfig.stopLossPercent) {
      return {
        passed: false,
        reason: `Stop-loss ${decision.exitPlan.stopLoss}% exceeds maximum ${this.tradingConfig.stopLossPercent}%`,
      };
    }

    return { passed: true };
  }

  /**
   * Check maximum concurrent positions
   */
  private checkMaxPositions(
    decision: TradingDecision,
    marketState: MarketState
  ): { passed: boolean; reason?: string } {
    if (decision.action === 'CLOSE' || decision.action === 'HOLD') {
      return { passed: true };
    }

    const currentPositions = marketState.account.positions.length;

    if (currentPositions >= this.tradingConfig.maxConcurrentPositions) {
      return {
        passed: false,
        reason: `Maximum concurrent positions (${this.tradingConfig.maxConcurrentPositions}) already reached`,
      };
    }

    return { passed: true };
  }

  /**
   * Check daily loss limit (circuit breaker)
   */
  private checkDailyLoss(marketState: MarketState): { passed: boolean; reason?: string } {
    if (!this.riskConfig.circuitBreakerEnabled) {
      return { passed: true };
    }

    const currentEquity = marketState.account.totalEquity;
    const dailyLoss = this.startOfDayEquity - currentEquity;
    const dailyLossPercent = (dailyLoss / this.startOfDayEquity) * 100;

    if (dailyLossPercent > this.riskConfig.maxDailyLossPercent) {
      return {
        passed: false,
        reason: `Circuit breaker triggered: Daily loss ${dailyLossPercent.toFixed(2)}% exceeds limit ${this.riskConfig.maxDailyLossPercent}%`,
      };
    }

    return { passed: true };
  }

  /**
   * Check portfolio exposure limits
   */
  private checkPortfolioExposure(
    decision: TradingDecision,
    marketState: MarketState
  ): { passed: boolean; reason?: string } {
    if (decision.action === 'CLOSE' || decision.action === 'HOLD') {
      return { passed: true };
    }

    const { account } = marketState;
    const marketPrice = marketState.pairs[decision.symbol]?.price || 0;

    // Calculate current total exposure
    const currentExposure = account.positions.reduce(
      (sum, pos) => sum + (pos.size * pos.currentPrice),
      0
    );

    // Calculate new position exposure
    const newPositionExposure = decision.quantity * marketPrice;

    // Calculate total exposure after new trade
    const totalExposure = currentExposure + newPositionExposure;
    const exposurePercent = (totalExposure / account.totalEquity) * 100;

    if (exposurePercent > this.riskConfig.maxPortfolioExposurePercent) {
      return {
        passed: false,
        reason: `Total portfolio exposure ${exposurePercent.toFixed(2)}% would exceed limit ${this.riskConfig.maxPortfolioExposurePercent}%`,
      };
    }

    return { passed: true };
  }

  /**
   * Check if short selling is allowed
   */
  private checkShortSelling(decision: TradingDecision): { passed: boolean; reason?: string } {
    if (!this.tradingConfig.enableShortSelling && decision.action === 'OPEN_SHORT') {
      return {
        passed: false,
        reason: 'Short selling is disabled in configuration',
      };
    }

    return { passed: true };
  }

  /**
   * Get start of current day timestamp
   */
  private getStartOfDay(): number {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return now.getTime();
  }
}
