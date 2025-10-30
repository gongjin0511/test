/**
 * Configuration loader and validator
 */

import dotenv from 'dotenv';
import { z } from 'zod';
import type { SystemConfig } from '../types/index.js';

// Load environment variables
dotenv.config();

// Zod schemas for validation
const OKXConfigSchema = z.object({
  apiKey: z.string().min(1, 'OKX API key is required'),
  secretKey: z.string().min(1, 'OKX secret key is required'),
  passphrase: z.string().min(1, 'OKX passphrase is required'),
  environment: z.enum(['demo', 'production']).default('demo'),
  testnet: z.boolean().optional(),
});

const AIConfigSchema = z.object({
  provider: z.enum(['anthropic', 'openai', 'custom']).default('anthropic'),
  apiKey: z.string().min(1, 'AI API key is required'),
  model: z.string().default('claude-sonnet-4.5'),
  temperature: z.number().min(0).max(2).optional().default(0.7),
  maxTokens: z.number().positive().optional().default(4000),
  customEndpoint: z.string().url().optional(),
});

const TradingConfigSchema = z.object({
  initialCapital: z.number().positive().default(10000),
  tradingPairs: z.array(z.string()).min(1, 'At least one trading pair required'),
  decisionIntervalMs: z.number().positive().default(180000), // 3 minutes
  mode: z.enum(['testnet', 'live']).default('testnet'),
  maxLeverage: z.number().min(1).max(125).default(5),
  maxPositionSizePercent: z.number().min(1).max(100).default(20),
  stopLossPercent: z.number().positive().default(5),
  takeProfitPercent: z.number().positive().default(10),
  maxConcurrentPositions: z.number().positive().default(3),
  enableShortSelling: z.boolean().default(true),
});

const RiskConfigSchema = z.object({
  maxDailyLossPercent: z.number().positive().default(10),
  maxDrawdownPercent: z.number().positive().default(20),
  maxPortfolioExposurePercent: z.number().min(1).max(100).default(80),
  requireStopLoss: z.boolean().default(true),
  minConfidenceThreshold: z.number().min(0).max(1).default(0.6),
  circuitBreakerEnabled: z.boolean().default(true),
});

const SystemConfigSchema = z.object({
  okx: OKXConfigSchema,
  ai: AIConfigSchema,
  trading: TradingConfigSchema,
  risk: RiskConfigSchema,
  database: z.object({
    path: z.string().default('./data/trading.db'),
  }),
  logging: z.object({
    level: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
    filePath: z.string().default('./logs/trading.log'),
  }),
  redis: z.object({
    url: z.string().default('redis://localhost:6379'),
    enabled: z.boolean().default(false),
  }).optional(),
});

/**
 * Parse trading pairs from comma-separated string
 */
function parseTradingPairs(pairsStr: string | undefined): string[] {
  if (!pairsStr) {
    return ['BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP'];
  }
  return pairsStr.split(',').map(pair => pair.trim()).filter(Boolean);
}

/**
 * Load and validate system configuration
 */
export function loadConfig(): SystemConfig {
  const config = {
    okx: {
      apiKey: process.env.OKX_API_KEY || '',
      secretKey: process.env.OKX_SECRET_KEY || '',
      passphrase: process.env.OKX_PASSPHRASE || '',
      environment: (process.env.OKX_API_ENV as 'demo' | 'production') || 'demo',
      testnet: process.env.OKX_API_ENV === 'demo',
    },
    ai: {
      provider: (process.env.AI_PROVIDER as 'anthropic' | 'openai' | 'custom') || 'anthropic',
      apiKey: process.env.AI_PROVIDER === 'anthropic'
        ? process.env.ANTHROPIC_API_KEY || ''
        : process.env.OPENAI_API_KEY || '',
      model: process.env.AI_MODEL || 'claude-sonnet-4.5',
      temperature: parseFloat(process.env.AI_TEMPERATURE || '0.7'),
      maxTokens: parseInt(process.env.AI_MAX_TOKENS || '4000', 10),
      customEndpoint: process.env.AI_CUSTOM_ENDPOINT,
    },
    trading: {
      initialCapital: parseFloat(process.env.INITIAL_CAPITAL || '10000'),
      tradingPairs: parseTradingPairs(process.env.TRADING_PAIRS),
      decisionIntervalMs: parseInt(process.env.DECISION_INTERVAL_MS || '180000', 10),
      mode: (process.env.TRADING_MODE as 'testnet' | 'live') || 'testnet',
      maxLeverage: parseInt(process.env.MAX_LEVERAGE || '5', 10),
      maxPositionSizePercent: parseFloat(process.env.MAX_POSITION_SIZE_PERCENTAGE || '20'),
      stopLossPercent: parseFloat(process.env.STOP_LOSS_PERCENTAGE || '5'),
      takeProfitPercent: parseFloat(process.env.TAKE_PROFIT_PERCENTAGE || '10'),
      maxConcurrentPositions: parseInt(process.env.MAX_CONCURRENT_POSITIONS || '3', 10),
      enableShortSelling: process.env.ENABLE_SHORT_SELLING !== 'false',
    },
    risk: {
      maxDailyLossPercent: parseFloat(process.env.MAX_DAILY_LOSS_PERCENT || '10'),
      maxDrawdownPercent: parseFloat(process.env.MAX_DRAWDOWN_PERCENT || '20'),
      maxPortfolioExposurePercent: parseFloat(process.env.MAX_PORTFOLIO_EXPOSURE_PERCENT || '80'),
      requireStopLoss: process.env.REQUIRE_STOP_LOSS !== 'false',
      minConfidenceThreshold: parseFloat(process.env.MIN_CONFIDENCE_THRESHOLD || '0.6'),
      circuitBreakerEnabled: process.env.CIRCUIT_BREAKER_ENABLED !== 'false',
    },
    database: {
      path: process.env.DB_PATH || './data/trading.db',
    },
    logging: {
      level: (process.env.LOG_LEVEL as 'debug' | 'info' | 'warn' | 'error') || 'info',
      filePath: process.env.LOG_FILE || './logs/trading.log',
    },
    redis: process.env.REDIS_ENABLED === 'true' ? {
      url: process.env.REDIS_URL || 'redis://localhost:6379',
      enabled: true,
    } : undefined,
  };

  // Validate configuration
  const result = SystemConfigSchema.safeParse(config);

  if (!result.success) {
    console.error('Configuration validation failed:');
    console.error(result.error.format());
    throw new Error('Invalid configuration. Please check your .env file.');
  }

  return result.data;
}

/**
 * Get configuration with caching
 */
let cachedConfig: SystemConfig | null = null;

export function getConfig(): SystemConfig {
  if (!cachedConfig) {
    cachedConfig = loadConfig();
  }
  return cachedConfig;
}

/**
 * Validate configuration without throwing
 */
export function validateConfig(): { valid: boolean; errors?: string[] } {
  try {
    loadConfig();
    return { valid: true };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        valid: false,
        errors: error.errors.map(e => `${e.path.join('.')}: ${e.message}`),
      };
    }
    return {
      valid: false,
      errors: [error instanceof Error ? error.message : 'Unknown error'],
    };
  }
}
