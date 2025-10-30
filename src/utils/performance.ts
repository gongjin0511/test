/**
 * Performance metrics calculator
 */

import type { PerformanceMetrics, TradeRecord, IDatabase } from '../types/index.js';

/**
 * Calculate performance metrics from trade history
 */
export async function calculatePerformanceMetrics(
  database: IDatabase,
  currentEquity: number,
  initialCapital: number
): Promise<PerformanceMetrics> {
  // Get all closed trades
  const closedTrades = await database.getTrades({ status: 'closed' });

  // Calculate basic metrics
  const totalTrades = closedTrades.length;
  const winningTrades = closedTrades.filter(t => (t.pnl || 0) > 0);
  const losingTrades = closedTrades.filter(t => (t.pnl || 0) < 0);

  const winCount = winningTrades.length;
  const lossCount = losingTrades.length;

  const totalPnl = closedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
  const totalPnlPercent = ((currentEquity - initialCapital) / initialCapital) * 100;

  const totalWins = winningTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
  const totalLosses = Math.abs(losingTrades.reduce((sum, t) => sum + (t.pnl || 0), 0));

  const averageWin = winCount > 0 ? totalWins / winCount : 0;
  const averageLoss = lossCount > 0 ? totalLosses / lossCount : 0;

  const winRate = totalTrades > 0 ? (winCount / totalTrades) * 100 : 0;
  const profitFactor = totalLosses > 0 ? totalWins / totalLosses : totalWins > 0 ? Infinity : 0;

  // Calculate Sharpe ratio (simplified)
  const sharpeRatio = calculateSharpeRatio(closedTrades);

  // Calculate max drawdown
  const { maxDrawdown, maxDrawdownPercent } = calculateMaxDrawdown(closedTrades, initialCapital);

  // Calculate daily PnL (last 24 hours)
  const dayAgo = Date.now() - 24 * 60 * 60 * 1000;
  const recentTrades = closedTrades.filter(t => t.timestamp >= dayAgo);
  const dailyPnl = recentTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);
  const dailyPnlPercent = (dailyPnl / initialCapital) * 100;

  return {
    timestamp: Date.now(),
    totalPnl,
    totalPnlPercent,
    sharpeRatio,
    winRate,
    totalTrades,
    winningTrades: winCount,
    losingTrades: lossCount,
    averageWin,
    averageLoss,
    profitFactor,
    maxDrawdown,
    maxDrawdownPercent,
    currentEquity,
    dailyPnl,
    dailyPnlPercent,
  };
}

/**
 * Calculate Sharpe ratio
 * Sharpe Ratio = (Average Return - Risk-Free Rate) / Standard Deviation of Returns
 */
function calculateSharpeRatio(trades: TradeRecord[]): number {
  if (trades.length < 2) {
    return 0;
  }

  // Calculate returns for each trade
  const returns = trades.map(t => t.pnlPercent || 0);

  // Calculate average return
  const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;

  // Calculate standard deviation
  const squaredDiffs = returns.map(r => Math.pow(r - avgReturn, 2));
  const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / returns.length;
  const stdDev = Math.sqrt(variance);

  if (stdDev === 0) {
    return 0;
  }

  // Assuming risk-free rate of 0% for simplicity
  const riskFreeRate = 0;

  // Annualize the Sharpe ratio (assuming trades are roughly daily)
  const sharpeRatio = (avgReturn - riskFreeRate) / stdDev;

  // Annualization factor (sqrt of 365 for daily returns)
  return sharpeRatio * Math.sqrt(365 / trades.length);
}

/**
 * Calculate maximum drawdown
 */
function calculateMaxDrawdown(
  trades: TradeRecord[],
  initialCapital: number
): { maxDrawdown: number; maxDrawdownPercent: number } {
  if (trades.length === 0) {
    return { maxDrawdown: 0, maxDrawdownPercent: 0 };
  }

  // Sort trades by timestamp
  const sortedTrades = [...trades].sort((a, b) => a.timestamp - b.timestamp);

  // Calculate equity curve
  let equity = initialCapital;
  let peak = initialCapital;
  let maxDrawdown = 0;

  for (const trade of sortedTrades) {
    equity += trade.pnl || 0;

    if (equity > peak) {
      peak = equity;
    }

    const drawdown = peak - equity;
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }

  const maxDrawdownPercent = peak > 0 ? (maxDrawdown / peak) * 100 : 0;

  return { maxDrawdown, maxDrawdownPercent };
}

/**
 * Format performance metrics for display
 */
export function formatPerformanceMetrics(metrics: PerformanceMetrics): string {
  return `
Performance Metrics:
  Total PnL: $${metrics.totalPnl.toFixed(2)} (${metrics.totalPnlPercent.toFixed(2)}%)
  Sharpe Ratio: ${metrics.sharpeRatio.toFixed(2)}
  Win Rate: ${metrics.winRate.toFixed(2)}%
  Total Trades: ${metrics.totalTrades} (${metrics.winningTrades}W / ${metrics.losingTrades}L)
  Average Win: $${metrics.averageWin.toFixed(2)}
  Average Loss: $${metrics.averageLoss.toFixed(2)}
  Profit Factor: ${metrics.profitFactor === Infinity ? '∞' : metrics.profitFactor.toFixed(2)}
  Max Drawdown: $${metrics.maxDrawdown.toFixed(2)} (${metrics.maxDrawdownPercent.toFixed(2)}%)
  Current Equity: $${metrics.currentEquity.toFixed(2)}
  Daily PnL: $${metrics.dailyPnl.toFixed(2)} (${metrics.dailyPnlPercent.toFixed(2)}%)
  `.trim();
}
