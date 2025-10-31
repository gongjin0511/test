/**
 * Enhanced Trading Orchestrator with Learning Loop
 * Integrates memory, post-trade analysis, and adaptive prompts
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
import { PostTradeAnalyzer } from '../learning/post-trade-analysis.js';

export class EnhancedTradingOrchestrator {
  private isRunning: boolean = false;
  private intervalId?: NodeJS.Timeout;
  private postTradeAnalyzer: PostTradeAnalyzer;

  constructor(
    private config: SystemConfig,
    private exchange: IExchangeClient,
    private aiProvider: IAIProvider,
    private riskManager: IRiskManager,
    private database: IDatabase,
    private logger: ILogger,
    private systemPrompt: string
  ) {
    this.postTradeAnalyzer = new PostTradeAnalyzer(database, logger);
  }

  /**
   * Start the trading system with learning loop
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      this.logger.warn('Trading system is already running');
      return;
    }

    this.logger.info('🚀 Starting enhanced trading system with learning capabilities...');

    try {
      // Test exchange connection
      const connected = await this.exchange.testConnection();
      if (!connected) {
        throw new Error('Failed to connect to exchange');
      }

      this.logger.info('✓ Connected to OKX exchange');

      // Initialize executor
      const executor = new TradingExecutor(this.exchange, this.database, this.logger);

      this.isRunning = true;

      // Log start event
      await this.database.saveDecision({
        timestamp: Date.now(),
        marketState: JSON.stringify({ event: 'system_started_with_learning' }),
        aiOutput: JSON.stringify({ event: 'system_started_with_learning' }),
        riskApproved: true,
      });

      this.logger.info('✓ Trading system started with learning loop enabled');

      // Run first decision cycle immediately
      await this.runEnhancedDecisionCycle(executor);

      // Schedule periodic decision cycles
      this.intervalId = setInterval(
        () => this.runEnhancedDecisionCycle(executor),
        this.config.trading.decisionIntervalMs
      );

      this.logger.info(
        `✓ Decision cycles scheduled every ${this.config.trading.decisionIntervalMs / 1000} seconds`
      );
      this.logger.info('✓ Memory system active - learning from every trade');
      this.logger.info('✓ Post-trade analysis enabled');
      this.logger.info('✓ Dynamic prompt adaptation active');

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

    this.logger.info('🛑 Stopping trading system...');

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

    this.logger.info('✓ Trading system stopped gracefully');
  }

  /**
   * Run enhanced decision cycle with learning
   */
  private async runEnhancedDecisionCycle(executor: TradingExecutor): Promise<void> {
    const cycleStartTime = Date.now();

    try {
      this.logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      this.logger.info('🔄 Starting enhanced decision cycle with learning');
      this.logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

      // Step 1: Collect market data
      this.logger.info('📊 Collecting market data...');
      const marketState = await this.collectMarketData();

      // Step 2: Monitor existing positions
      this.logger.info('👀 Monitoring existing positions...');
      await executor.monitorPositions(marketState);

      // Step 3: Generate AI decision with memory and learning
      this.logger.info('🧠 Generating AI decision (with memory & learning)...');
      const aiStartTime = Date.now();
      const decision = await this.aiProvider.generateDecision(marketState, this.systemPrompt);
      const aiExecutionTime = Date.now() - aiStartTime;

      this.logger.info('✓ AI decision generated', {
        action: decision.action,
        symbol: decision.symbol,
        confidence: decision.confidence.toFixed(2),
        executionTime: `${aiExecutionTime}ms`,
      });

      // Log self-reflection if present
      if ((decision as any).selfReflection) {
        this.logger.info('💭 AI Self-Reflection:', {
          reflection: (decision as any).selfReflection,
        });
      }

      // Step 4: Validate with risk management
      this.logger.info('🛡️  Validating decision with risk management...');
      const validation = this.riskManager.validateDecision(decision, marketState);

      // Step 5: Save decision to database
      const decisionRecord: DecisionRecord = {
        timestamp: Date.now(),
        marketState: JSON.stringify(marketState),
        aiOutput: JSON.stringify(decision),
        riskApproved: validation.approved,
        rejectionReason: validation.reason,
        executionTime: aiExecutionTime,
      };

      await this.database.saveDecision(decisionRecord);

      // Step 6: Execute trade if approved
      if (validation.approved) {
        this.logger.info('✅ Decision approved - executing trade...');

        const trade = await executor.executeDecision(decision, marketState);

        if (trade) {
          this.logger.info('✓ Trade executed successfully', {
            tradeId: trade.id,
            symbol: trade.symbol,
            action: trade.action,
            quantity: trade.quantity,
            entryPrice: trade.entryPrice.toFixed(2),
            leverage: trade.leverage,
          });

          // Step 7: Perform post-trade analysis on completed trades
          const closedTrades = await this.database.getTrades({
            status: 'closed',
            limit: 1,
          });

          if (closedTrades.length > 0) {
            const lastClosedTrade = closedTrades[0];
            this.logger.info('📈 Performing post-trade analysis on last closed trade...');

            const analysis = await this.postTradeAnalyzer.analyzeTrade(lastClosedTrade);

            this.logger.info('✓ Post-trade analysis completed', {
              outcome: analysis.outcome,
              keyTakeaways: analysis.keyTakeaways.slice(0, 2),
            });

            // Log detailed analysis for learning
            this.logger.debug('Detailed trade analysis', {
              analysis: analysis.analysis,
              whatWorked: analysis.whatWorked,
              whatDidntWork: analysis.whatDidntWork,
              recommendations: analysis.recommendations,
              emotionalFactors: analysis.emotionalFactors,
            });
          }
        }
      } else {
        this.logger.warn('❌ Decision rejected by risk management', {
          reason: validation.reason,
          warnings: validation.warnings,
        });
      }

      // Step 8: Update performance metrics
      this.logger.info('📊 Updating performance metrics...');
      await this.updatePerformanceMetrics(marketState);

      // Step 9: Update risk metrics
      const riskMetrics = this.riskManager.updateRiskMetrics(marketState);
      this.logger.info('✓ Risk metrics updated', {
        exposurePercent: `${riskMetrics.exposurePercent.toFixed(2)}%`,
        portfolioLeverage: `${riskMetrics.portfolioLeverage.toFixed(2)}x`,
        availableCapital: `$${riskMetrics.availableRiskCapital.toFixed(2)}`,
      });

      // Step 10: Display current performance summary
      const performanceMetrics = await this.database.getLatestPerformance();
      if (performanceMetrics) {
        this.logger.info('📈 Current Performance Summary', {
          totalPnL: `$${performanceMetrics.totalPnl.toFixed(2)} (${performanceMetrics.totalPnlPercent.toFixed(2)}%)`,
          sharpeRatio: performanceMetrics.sharpeRatio.toFixed(2),
          winRate: `${performanceMetrics.winRate.toFixed(1)}%`,
          totalTrades: performanceMetrics.totalTrades,
        });
      }

      const cycleDuration = Date.now() - cycleStartTime;
      this.logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      this.logger.info(`✅ Decision cycle completed in ${cycleDuration}ms`);
      this.logger.info('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    } catch (error) {
      this.logger.error('❌ Error in enhanced decision cycle', {
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

      this.logger.debug('Performance metrics saved', {
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

  /**
   * Get current system status for monitoring
   */
  async getSystemStatus() {
    const performance = await this.database.getLatestPerformance();
    const recentTrades = await this.database.getTrades({ limit: 5 });
    const recentDecisions = await this.database.getDecisions({ limit: 5 });

    return {
      isRunning: this.isRunning,
      performance,
      recentTrades,
      recentDecisions,
      config: {
        decisionIntervalMs: this.config.trading.decisionIntervalMs,
        tradingPairs: this.config.trading.tradingPairs,
        maxLeverage: this.config.trading.maxLeverage,
      },
    };
  }
}
