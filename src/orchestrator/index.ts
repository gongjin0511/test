/**
 * Trading Orchestrator
 * Main control loop that coordinates all system components
 */

import type {
  SystemConfig,
  MarketState,
  TradingDecision,
  DecisionRecord,
  IExchangeClient,
  IDatabase,
  ILogger,
  IAIProvider,
  IRiskManager,
} from '../types/index.js';
import { TradingExecutor } from '../trading/executor.js';
import { calculatePerformanceMetrics } from '../utils/performance.js';

export class TradingOrchestrator {
  private isRunning: boolean = false;
  private intervalId?: NodeJS.Timeout;

  constructor(
    private config: SystemConfig,
    private exchange: IExchangeClient,
    private aiProvider: IAIProvider,
    private riskManager: IRiskManager,
    private database: IDatabase,
    private logger: ILogger,
    private systemPrompt: string
  ) {}

  /**
   * Start the trading system
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      this.logger.warn('Trading system is already running');
      return;
    }

    this.logger.info('Starting trading system...');

    try {
      // Test exchange connection
      const connected = await this.exchange.testConnection();
      if (!connected) {
        throw new Error('Failed to connect to exchange');
      }

      this.logger.info('Connected to OKX exchange');

      // Initialize executor
      const executor = new TradingExecutor(this.exchange, this.database, this.logger);

      this.isRunning = true;

      // Log start event
      await this.database.saveDecision({
        timestamp: Date.now(),
        marketState: JSON.stringify({ event: 'system_started' }),
        aiOutput: JSON.stringify({ event: 'system_started' }),
        riskApproved: true,
      });

      this.logger.info('Trading system started successfully');

      // Run first decision cycle immediately
      await this.runDecisionCycle(executor);

      // Schedule periodic decision cycles
      this.intervalId = setInterval(
        () => this.runDecisionCycle(executor),
        this.config.trading.decisionIntervalMs
      );

      this.logger.info(
        `Decision cycles scheduled every ${this.config.trading.decisionIntervalMs / 1000} seconds`
      );
    } catch (error) {
      this.logger.error('Failed to start trading system', {
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      this.isRunning = false;
      throw error;
    }
  }

  /**
   * Stop the trading system
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      this.logger.warn('Trading system is not running');
      return;
    }

    this.logger.info('Stopping trading system...');

    // Clear interval
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = undefined;
    }

    this.isRunning = false;

    // Log stop event
    await this.database.saveDecision({
      timestamp: Date.now(),
      marketState: JSON.stringify({ event: 'system_stopped' }),
      aiOutput: JSON.stringify({ event: 'system_stopped' }),
      riskApproved: true,
    });

    this.logger.info('Trading system stopped');
  }

  /**
   * Run a single decision cycle
   */
  private async runDecisionCycle(executor: TradingExecutor): Promise<void> {
    const cycleStartTime = Date.now();

    try {
      this.logger.info('--- Starting decision cycle ---');

      // 1. Collect market data
      this.logger.debug('Collecting market data...');
      const marketState = await this.collectMarketData();

      // 2. Monitor existing positions
      this.logger.debug('Monitoring existing positions...');
      await executor.monitorPositions(marketState);

      // 3. Generate AI decision
      this.logger.debug('Generating AI decision...');
      const aiStartTime = Date.now();
      const decision = await this.aiProvider.generateDecision(marketState, this.systemPrompt);
      const aiExecutionTime = Date.now() - aiStartTime;

      this.logger.info('AI decision generated', {
        action: decision.action,
        symbol: decision.symbol,
        confidence: decision.confidence,
        executionTime: aiExecutionTime,
      });

      // 4. Validate with risk management
      this.logger.debug('Validating decision with risk management...');
      const validation = this.riskManager.validateDecision(decision, marketState);

      // 5. Save decision to database
      const decisionRecord: DecisionRecord = {
        timestamp: Date.now(),
        marketState: JSON.stringify(marketState),
        aiOutput: JSON.stringify(decision),
        riskApproved: validation.approved,
        rejectionReason: validation.reason,
        executionTime: aiExecutionTime,
      };

      await this.database.saveDecision(decisionRecord);

      // 6. Execute trade if approved
      if (validation.approved) {
        this.logger.info('Decision approved, executing trade...');

        const trade = await executor.executeDecision(decision, marketState);

        if (trade) {
          this.logger.info('Trade executed successfully', {
            tradeId: trade.id,
            symbol: trade.symbol,
            action: trade.action,
            quantity: trade.quantity,
          });
        }
      } else {
        this.logger.warn('Decision rejected by risk management', {
          reason: validation.reason,
          warnings: validation.warnings,
        });
      }

      // 7. Update performance metrics
      this.logger.debug('Updating performance metrics...');
      await this.updatePerformanceMetrics(marketState);

      // 8. Update risk metrics
      const riskMetrics = this.riskManager.updateRiskMetrics(marketState);
      this.logger.debug('Risk metrics updated', {
        exposurePercent: riskMetrics.exposurePercent.toFixed(2),
        portfolioLeverage: riskMetrics.portfolioLeverage.toFixed(2),
      });

      const cycleDuration = Date.now() - cycleStartTime;
      this.logger.info(`--- Decision cycle completed in ${cycleDuration}ms ---`);
    } catch (error) {
      this.logger.error('Error in decision cycle', {
        error: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : undefined,
      });

      // Log error but continue running
      await this.database.saveDecision({
        timestamp: Date.now(),
        marketState: JSON.stringify({ error: 'cycle_error' }),
        aiOutput: JSON.stringify({
          error: error instanceof Error ? error.message : 'Unknown error',
        }),
        riskApproved: false,
        rejectionReason: 'Cycle error occurred',
      });
    }
  }

  /**
   * Collect market data from exchange
   */
  private async collectMarketData(): Promise<MarketState> {
    // Get account state
    const account = await this.exchange.getAccountState();

    // Get market data for all trading pairs
    const pairs: Record<string, any> = {};

    for (const symbol of this.config.trading.tradingPairs) {
      try {
        const marketData = await this.exchange.getMarketData(symbol);
        pairs[symbol] = marketData;
      } catch (error) {
        this.logger.error(`Failed to get market data for ${symbol}`, {
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    }

    // Get latest performance metrics
    const performanceMetrics = await this.database.getLatestPerformance();

    return {
      timestamp: Date.now(),
      pairs,
      account,
      performanceMetrics: performanceMetrics || undefined,
    };
  }

  /**
   * Update performance metrics
   */
  private async updatePerformanceMetrics(marketState: MarketState): Promise<void> {
    try {
      const metrics = await calculatePerformanceMetrics(
        this.database,
        marketState.account.totalEquity,
        this.config.trading.initialCapital
      );

      await this.database.savePerformance(metrics);

      this.logger.debug('Performance metrics', {
        totalPnl: metrics.totalPnl.toFixed(2),
        sharpeRatio: metrics.sharpeRatio.toFixed(2),
        winRate: metrics.winRate.toFixed(2),
      });
    } catch (error) {
      this.logger.error('Failed to update performance metrics', {
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  /**
   * Check if system is running
   */
  isSystemRunning(): boolean {
    return this.isRunning;
  }
}
