#!/usr/bin/env node

/**
 * OKX AI Trading System
 * Main entry point
 */

import { getConfig } from './config/index.js';
import { initLogger } from './utils/logger.js';
import { initDatabase } from './database/index.js';
import { createOKXClient } from './exchange/okx-client.js';
import { AnthropicProvider } from './ai/providers/anthropic.js';
import { SYSTEM_PROMPT } from './ai/system-prompt.js';
import { RiskManager } from './risk/risk-manager.js';
import { TradingOrchestrator } from './orchestrator/index.js';

/**
 * Main function
 */
async function main() {
  console.log('='.repeat(60));
  console.log('  OKX AI Trading System');
  console.log('  Inspired by nof1.ai Alpha Arena');
  console.log('='.repeat(60));
  console.log();

  try {
    // 1. Load configuration
    console.log('📋 Loading configuration...');
    const config = getConfig();
    console.log(`   - Trading mode: ${config.trading.mode}`);
    console.log(`   - Initial capital: $${config.trading.initialCapital}`);
    console.log(`   - Trading pairs: ${config.trading.tradingPairs.join(', ')}`);
    console.log(`   - AI provider: ${config.ai.provider} (${config.ai.model})`);
    console.log(`   - Decision interval: ${config.trading.decisionIntervalMs / 1000}s`);
    console.log();

    // 2. Initialize logger
    console.log('📝 Initializing logger...');
    const logger = await initLogger(config.logging.level, config.logging.filePath);
    logger.info('Logger initialized');
    console.log(`   - Log level: ${config.logging.level}`);
    console.log(`   - Log file: ${config.logging.filePath}`);
    console.log();

    // 3. Initialize database
    console.log('💾 Initializing database...');
    const database = await initDatabase(config.database.path);
    logger.info('Database initialized');
    console.log(`   - Database path: ${config.database.path}`);
    console.log();

    // 4. Initialize exchange client
    console.log('🔌 Connecting to OKX exchange...');
    const exchange = createOKXClient(config.okx);
    const connected = await exchange.testConnection();
    if (!connected) {
      throw new Error('Failed to connect to OKX exchange');
    }
    logger.info('Connected to OKX exchange');
    console.log('   - Connection successful');
    console.log();

    // 5. Initialize AI provider
    console.log('🤖 Initializing AI provider...');
    const aiProvider = new AnthropicProvider(config.ai);
    logger.info('AI provider initialized', { provider: config.ai.provider });
    console.log(`   - Provider: ${config.ai.provider}`);
    console.log(`   - Model: ${config.ai.model}`);
    console.log();

    // 6. Initialize risk manager
    console.log('🛡️  Initializing risk manager...');
    const riskManager = new RiskManager(
      config.risk,
      config.trading,
      logger,
      config.trading.initialCapital
    );
    logger.info('Risk manager initialized');
    console.log('   - Max leverage: ' + config.trading.maxLeverage + 'x');
    console.log('   - Max position size: ' + config.trading.maxPositionSizePercent + '%');
    console.log('   - Circuit breaker: ' + (config.risk.circuitBreakerEnabled ? 'enabled' : 'disabled'));
    console.log();

    // 7. Create orchestrator
    console.log('🎯 Creating trading orchestrator...');
    const orchestrator = new TradingOrchestrator(
      config,
      exchange,
      aiProvider,
      riskManager,
      database,
      logger,
      SYSTEM_PROMPT
    );
    logger.info('Trading orchestrator created');
    console.log();

    // 8. Start trading system
    console.log('🚀 Starting trading system...');
    console.log();
    await orchestrator.start();

    // Handle graceful shutdown
    const shutdown = async (signal: string) => {
      console.log();
      console.log(`\n${signal} received, shutting down gracefully...`);
      logger.info(`Shutdown signal received: ${signal}`);

      await orchestrator.stop();
      database.close();

      console.log('System stopped successfully');
      logger.info('System stopped successfully');

      process.exit(0);
    };

    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));

    // Keep process alive
    console.log('✅ Trading system is now running');
    console.log('   Press Ctrl+C to stop');
    console.log();
    console.log('='.repeat(60));
    console.log();

    logger.info('Trading system is running');
  } catch (error) {
    console.error();
    console.error('❌ Fatal error:', error instanceof Error ? error.message : 'Unknown error');
    console.error();

    if (error instanceof Error && error.stack) {
      console.error(error.stack);
    }

    process.exit(1);
  }
}

// Run main function
main().catch(error => {
  console.error('Unhandled error:', error);
  process.exit(1);
});
