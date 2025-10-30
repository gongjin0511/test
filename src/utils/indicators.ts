/**
 * Technical indicators calculator
 */

import type { OHLCV, TechnicalIndicators } from '../types/index.js';

/**
 * Simple Moving Average (SMA)
 */
export function calculateSMA(prices: number[], period: number): number | undefined {
  if (prices.length < period) {
    return undefined;
  }

  const slice = prices.slice(-period);
  const sum = slice.reduce((acc, price) => acc + price, 0);
  return sum / period;
}

/**
 * Exponential Moving Average (EMA)
 */
export function calculateEMA(prices: number[], period: number): number | undefined {
  if (prices.length < period) {
    return undefined;
  }

  const multiplier = 2 / (period + 1);
  let ema = calculateSMA(prices.slice(0, period), period);

  if (ema === undefined) {
    return undefined;
  }

  for (let i = period; i < prices.length; i++) {
    ema = (prices[i] - ema) * multiplier + ema;
  }

  return ema;
}

/**
 * Relative Strength Index (RSI)
 */
export function calculateRSI(prices: number[], period: number = 14): number | undefined {
  if (prices.length < period + 1) {
    return undefined;
  }

  const changes: number[] = [];
  for (let i = 1; i < prices.length; i++) {
    changes.push(prices[i] - prices[i - 1]);
  }

  const gains: number[] = [];
  const losses: number[] = [];

  for (const change of changes) {
    gains.push(change > 0 ? change : 0);
    losses.push(change < 0 ? Math.abs(change) : 0);
  }

  const avgGain = calculateSMA(gains, period);
  const avgLoss = calculateSMA(losses, period);

  if (avgGain === undefined || avgLoss === undefined || avgLoss === 0) {
    return undefined;
  }

  const rs = avgGain / avgLoss;
  const rsi = 100 - (100 / (1 + rs));

  return rsi;
}

/**
 * Moving Average Convergence Divergence (MACD)
 */
export function calculateMACD(
  prices: number[],
  fastPeriod: number = 12,
  slowPeriod: number = 26,
  signalPeriod: number = 9
): { macd: number; signal: number; histogram: number } | undefined {
  const fastEMA = calculateEMA(prices, fastPeriod);
  const slowEMA = calculateEMA(prices, slowPeriod);

  if (fastEMA === undefined || slowEMA === undefined) {
    return undefined;
  }

  const macdLine = fastEMA - slowEMA;

  // For signal line, we'd need to calculate EMA of MACD values
  // This is a simplified version using the current MACD value
  const signalLine = macdLine; // Simplified

  const histogram = macdLine - signalLine;

  return {
    macd: macdLine,
    signal: signalLine,
    histogram,
  };
}

/**
 * Bollinger Bands
 */
export function calculateBollingerBands(
  prices: number[],
  period: number = 20,
  stdDev: number = 2
): { upper: number; middle: number; lower: number } | undefined {
  const sma = calculateSMA(prices, period);

  if (sma === undefined) {
    return undefined;
  }

  const slice = prices.slice(-period);

  // Calculate standard deviation
  const squaredDiffs = slice.map(price => Math.pow(price - sma, 2));
  const variance = squaredDiffs.reduce((acc, val) => acc + val, 0) / period;
  const standardDeviation = Math.sqrt(variance);

  return {
    upper: sma + (standardDeviation * stdDev),
    middle: sma,
    lower: sma - (standardDeviation * stdDev),
  };
}

/**
 * Average True Range (ATR) - measures volatility
 */
export function calculateATR(candles: OHLCV[], period: number = 14): number | undefined {
  if (candles.length < period + 1) {
    return undefined;
  }

  const trueRanges: number[] = [];

  for (let i = 1; i < candles.length; i++) {
    const current = candles[i];
    const previous = candles[i - 1];

    const highLow = current.high - current.low;
    const highClose = Math.abs(current.high - previous.close);
    const lowClose = Math.abs(current.low - previous.close);

    const trueRange = Math.max(highLow, highClose, lowClose);
    trueRanges.push(trueRange);
  }

  return calculateSMA(trueRanges, period);
}

/**
 * Calculate all technical indicators for a symbol
 */
export function calculateAllIndicators(
  closePrices: number[],
  candles?: OHLCV[]
): TechnicalIndicators {
  const indicators: TechnicalIndicators = {
    sma20: calculateSMA(closePrices, 20),
    sma50: calculateSMA(closePrices, 50),
    ema12: calculateEMA(closePrices, 12),
    ema26: calculateEMA(closePrices, 26),
    rsi: calculateRSI(closePrices, 14),
    macd: calculateMACD(closePrices),
    bollingerBands: calculateBollingerBands(closePrices, 20, 2),
  };

  if (candles && candles.length > 0) {
    indicators.atr = calculateATR(candles, 14);
  }

  return indicators;
}

/**
 * Detect price trend based on moving averages
 */
export function detectTrend(closePrices: number[]): 'bullish' | 'bearish' | 'neutral' {
  const sma20 = calculateSMA(closePrices, 20);
  const sma50 = calculateSMA(closePrices, 50);
  const currentPrice = closePrices[closePrices.length - 1];

  if (sma20 === undefined || sma50 === undefined) {
    return 'neutral';
  }

  // Bullish: Price > SMA20 > SMA50
  if (currentPrice > sma20 && sma20 > sma50) {
    return 'bullish';
  }

  // Bearish: Price < SMA20 < SMA50
  if (currentPrice < sma20 && sma20 < sma50) {
    return 'bearish';
  }

  return 'neutral';
}

/**
 * Calculate price change percentage
 */
export function calculatePriceChange(currentPrice: number, previousPrice: number): number {
  return ((currentPrice - previousPrice) / previousPrice) * 100;
}

/**
 * Calculate volatility (standard deviation of returns)
 */
export function calculateVolatility(prices: number[], period: number = 20): number | undefined {
  if (prices.length < period) {
    return undefined;
  }

  const slice = prices.slice(-period);
  const returns: number[] = [];

  for (let i = 1; i < slice.length; i++) {
    const returnPct = (slice[i] - slice[i - 1]) / slice[i - 1];
    returns.push(returnPct);
  }

  const meanReturn = returns.reduce((acc, r) => acc + r, 0) / returns.length;
  const squaredDiffs = returns.map(r => Math.pow(r - meanReturn, 2));
  const variance = squaredDiffs.reduce((acc, val) => acc + val, 0) / returns.length;

  return Math.sqrt(variance);
}
