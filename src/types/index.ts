/**
 * Core type definitions for the OKX AI Trading System
 */

// ==================== Trading Types ====================

export type TradingAction = 'OPEN_LONG' | 'OPEN_SHORT' | 'CLOSE' | 'HOLD';
export type OrderSide = 'buy' | 'sell';
export type OrderType = 'market' | 'limit';
export type PositionSide = 'long' | 'short' | 'net';

export interface TradingPair {
  symbol: string;        // e.g., 'BTC-USDT-SWAP'
  baseCurrency: string;  // e.g., 'BTC'
  quoteCurrency: string; // e.g., 'USDT'
  contractType: string;  // e.g., 'SWAP' (perpetual)
}

export interface TradingDecision {
  action: TradingAction;
  symbol: string;
  quantity: number;      // Size in contracts or base currency
  leverage: number;      // 1-125 (OKX supports up to 125x)
  confidence: number;    // 0-1
  reasoning: string;     // AI's explanation
  exitPlan: {
    takeProfit: number;     // Target profit percentage
    stopLoss: number;       // Stop loss percentage
    invalidation: string;   // Conditions to exit early
  };
  metadata?: {
    timestamp: number;
    modelVersion?: string;
    temperature?: number;
  };
}

// ==================== Market Data Types ====================

export interface OHLCV {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface OrderBookLevel {
  price: number;
  quantity: number;
}

export interface OrderBook {
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
  timestamp: number;
}

export interface TechnicalIndicators {
  sma20?: number;      // Simple Moving Average (20 periods)
  sma50?: number;      // Simple Moving Average (50 periods)
  ema12?: number;      // Exponential Moving Average (12 periods)
  ema26?: number;      // Exponential Moving Average (26 periods)
  rsi?: number;        // Relative Strength Index (14 periods)
  macd?: {
    macd: number;
    signal: number;
    histogram: number;
  };
  bollingerBands?: {
    upper: number;
    middle: number;
    lower: number;
  };
  atr?: number;        // Average True Range (volatility)
}

export interface MarketSnapshot {
  symbol: string;
  price: number;
  priceChange24h: number;      // Percentage
  volume24h: number;
  high24h: number;
  low24h: number;
  fundingRate?: number;        // For perpetual futures
  openInterest?: number;
  indicators: TechnicalIndicators;
  orderBook?: OrderBook;
  recentCandles?: OHLCV[];     // Last N candles
}

export interface AccountPosition {
  symbol: string;
  side: PositionSide;
  size: number;              // Position size in contracts
  entryPrice: number;
  currentPrice: number;
  leverage: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
  liquidationPrice?: number;
  timestamp: number;
}

export interface AccountState {
  totalEquity: number;
  availableBalance: number;
  usedMargin: number;
  unrealizedPnl: number;
  positions: AccountPosition[];
  openOrdersCount: number;
}

export interface MarketState {
  timestamp: number;
  pairs: Record<string, MarketSnapshot>;
  account: AccountState;
  performanceMetrics?: PerformanceMetrics;
}

// ==================== Performance & Risk Types ====================

export interface TradeRecord {
  id?: number;
  timestamp: number;
  symbol: string;
  action: TradingAction;
  side: OrderSide;
  quantity: number;
  entryPrice: number;
  exitPrice?: number;
  leverage: number;
  pnl?: number;
  pnlPercent?: number;
  confidence: number;
  reasoning: string;
  exitPlan: TradingDecision['exitPlan'];
  status: 'open' | 'closed' | 'cancelled';
  closeReason?: string;
  duration?: number;  // In milliseconds
}

export interface DecisionRecord {
  id?: number;
  timestamp: number;
  marketState: string;      // JSON stringified MarketState
  aiOutput: string;         // JSON stringified TradingDecision
  riskApproved: boolean;
  rejectionReason?: string;
  executionTime?: number;   // Time taken to generate decision (ms)
}

export interface PerformanceMetrics {
  timestamp: number;
  totalPnl: number;
  totalPnlPercent: number;
  sharpeRatio: number;
  winRate: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  averageWin: number;
  averageLoss: number;
  profitFactor: number;     // Total wins / Total losses
  maxDrawdown: number;
  maxDrawdownPercent: number;
  currentEquity: number;
  dailyPnl: number;
  dailyPnlPercent: number;
}

export interface RiskMetrics {
  currentExposure: number;      // Total position value
  exposurePercent: number;      // As % of equity
  maxSinglePositionSize: number;
  portfolioLeverage: number;    // Effective leverage across all positions
  availableRiskCapital: number;
  correlationRisk?: number;     // Correlation between positions
}

// ==================== Configuration Types ====================

export interface OKXConfig {
  apiKey: string;
  secretKey: string;
  passphrase: string;
  environment: 'demo' | 'production';
  testnet?: boolean;
}

export interface AIConfig {
  provider: 'anthropic' | 'openai' | 'custom';
  apiKey: string;
  model: string;
  temperature?: number;
  maxTokens?: number;
  customEndpoint?: string;
}

export interface TradingConfig {
  initialCapital: number;
  tradingPairs: string[];
  decisionIntervalMs: number;
  mode: 'testnet' | 'live';
  maxLeverage: number;
  maxPositionSizePercent: number;  // Max % of capital per position
  stopLossPercent: number;
  takeProfitPercent: number;
  maxConcurrentPositions: number;
  enableShortSelling: boolean;
}

export interface RiskConfig {
  maxDailyLossPercent: number;
  maxDrawdownPercent: number;
  maxPortfolioExposurePercent: number;
  requireStopLoss: boolean;
  minConfidenceThreshold: number;   // Min AI confidence to execute
  circuitBreakerEnabled: boolean;
}

export interface SystemConfig {
  okx: OKXConfig;
  ai: AIConfig;
  trading: TradingConfig;
  risk: RiskConfig;
  database: {
    path: string;
  };
  logging: {
    level: 'debug' | 'info' | 'warn' | 'error';
    filePath: string;
  };
  redis?: {
    url: string;
    enabled: boolean;
  };
}

// ==================== Service Interfaces ====================

export interface IAIProvider {
  generateDecision(marketState: MarketState, systemPrompt: string): Promise<TradingDecision>;
  validateResponse(response: unknown): TradingDecision;
}

export interface IExchangeClient {
  // Market Data
  getMarketData(symbol: string): Promise<MarketSnapshot>;
  getAccountState(): Promise<AccountState>;
  getPositions(): Promise<AccountPosition[]>;

  // Trading
  placeOrder(params: OrderParams): Promise<OrderResult>;
  cancelOrder(orderId: string, symbol: string): Promise<void>;
  closePosition(symbol: string): Promise<OrderResult>;

  // Utility
  testConnection(): Promise<boolean>;
}

export interface OrderParams {
  symbol: string;
  side: OrderSide;
  type: OrderType;
  quantity: number;
  price?: number;          // Required for limit orders
  leverage?: number;
  stopLoss?: number;
  takeProfit?: number;
  positionSide?: PositionSide;
}

export interface OrderResult {
  orderId: string;
  symbol: string;
  status: 'filled' | 'partially_filled' | 'pending' | 'cancelled' | 'rejected';
  filledQuantity: number;
  averagePrice: number;
  timestamp: number;
  fee?: number;
}

export interface IRiskManager {
  validateDecision(decision: TradingDecision, marketState: MarketState): RiskValidationResult;
  checkCircuitBreaker(): boolean;
  updateRiskMetrics(marketState: MarketState): RiskMetrics;
}

export interface RiskValidationResult {
  approved: boolean;
  reason?: string;
  adjustedDecision?: Partial<TradingDecision>;  // Modified decision if needed
  warnings?: string[];
}

export interface IDatabase {
  saveTrade(trade: TradeRecord): Promise<number>;
  saveDecision(decision: DecisionRecord): Promise<number>;
  savePerformance(metrics: PerformanceMetrics): Promise<void>;

  getTrades(filter?: TradeFilter): Promise<TradeRecord[]>;
  getDecisions(filter?: DecisionFilter): Promise<DecisionRecord[]>;
  getLatestPerformance(): Promise<PerformanceMetrics | null>;

  updateTradeStatus(tradeId: number, status: TradeRecord['status'], exitData?: Partial<TradeRecord>): Promise<void>;
}

export interface TradeFilter {
  symbol?: string;
  status?: TradeRecord['status'];
  fromTimestamp?: number;
  toTimestamp?: number;
  limit?: number;
}

export interface DecisionFilter {
  riskApproved?: boolean;
  fromTimestamp?: number;
  toTimestamp?: number;
  limit?: number;
}

export interface ILogger {
  debug(message: string, meta?: unknown): void;
  info(message: string, meta?: unknown): void;
  warn(message: string, meta?: unknown): void;
  error(message: string, meta?: unknown): void;
}

// ==================== Event Types ====================

export type SystemEvent =
  | { type: 'system_started'; timestamp: number }
  | { type: 'system_stopped'; timestamp: number }
  | { type: 'decision_generated'; decision: TradingDecision; timestamp: number }
  | { type: 'decision_rejected'; decision: TradingDecision; reason: string; timestamp: number }
  | { type: 'trade_executed'; trade: TradeRecord; timestamp: number }
  | { type: 'trade_closed'; trade: TradeRecord; timestamp: number }
  | { type: 'circuit_breaker_triggered'; reason: string; timestamp: number }
  | { type: 'error_occurred'; error: Error; context: string; timestamp: number };

// ==================== Error Types ====================

export class TradingError extends Error {
  constructor(message: string, public code: string, public details?: unknown) {
    super(message);
    this.name = 'TradingError';
  }
}

export class ExchangeError extends TradingError {
  constructor(message: string, details?: unknown) {
    super(message, 'EXCHANGE_ERROR', details);
    this.name = 'ExchangeError';
  }
}

export class RiskViolationError extends TradingError {
  constructor(message: string, details?: unknown) {
    super(message, 'RISK_VIOLATION', details);
    this.name = 'RiskViolationError';
  }
}

export class AIProviderError extends TradingError {
  constructor(message: string, details?: unknown) {
    super(message, 'AI_PROVIDER_ERROR', details);
    this.name = 'AIProviderError';
  }
}
