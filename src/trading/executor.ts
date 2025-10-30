/**
 * Trading Execution Pipeline
 * Executes approved trading decisions
 */

import type {
  IExchangeClient,
  IDatabase,
  ILogger,
  TradingDecision,
  MarketState,
  TradeRecord,
  OrderParams,
  OrderSide,
} from '../types/index.js';
import { ExchangeError } from '../types/index.js';

export class TradingExecutor {
  constructor(
    private exchange: IExchangeClient,
    private database: IDatabase,
    private logger: ILogger
  ) {}

  /**
   * Execute a trading decision
   */
  async executeDecision(
    decision: TradingDecision,
    marketState: MarketState
  ): Promise<TradeRecord | null> {
    // Handle HOLD action
    if (decision.action === 'HOLD') {
      this.logger.info('Decision is HOLD, no trade executed');
      return null;
    }

    // Handle CLOSE action
    if (decision.action === 'CLOSE') {
      return await this.closePosition(decision);
    }

    // Handle OPEN_LONG or OPEN_SHORT
    return await this.openPosition(decision, marketState);
  }

  /**
   * Open a new position
   */
  private async openPosition(
    decision: TradingDecision,
    marketState: MarketState
  ): Promise<TradeRecord> {
    const { symbol, quantity, leverage, action, confidence, reasoning, exitPlan } = decision;

    // Determine order side
    const side: OrderSide = action === 'OPEN_LONG' ? 'buy' : 'sell';

    // Get current market price
    const marketPrice = marketState.pairs[symbol]?.price;
    if (!marketPrice) {
      throw new ExchangeError(`Market price not available for ${symbol}`);
    }

    this.logger.info('Opening position', {
      symbol,
      side,
      quantity,
      leverage,
      confidence,
    });

    try {
      // Prepare order parameters
      const orderParams: OrderParams = {
        symbol,
        side,
        type: 'market', // Use market orders for immediate execution
        quantity,
        leverage,
        // Note: Stop-loss and take-profit orders would be placed separately
      };

      // Place order on exchange
      const orderResult = await this.exchange.placeOrder(orderParams);

      this.logger.info('Order executed successfully', {
        orderId: orderResult.orderId,
        filledQuantity: orderResult.filledQuantity,
        averagePrice: orderResult.averagePrice,
      });

      // Create trade record
      const trade: TradeRecord = {
        timestamp: Date.now(),
        symbol,
        action,
        side,
        quantity: orderResult.filledQuantity,
        entryPrice: orderResult.averagePrice,
        leverage,
        confidence,
        reasoning,
        exitPlan,
        status: 'open',
      };

      // Save to database
      const tradeId = await this.database.saveTrade(trade);
      trade.id = tradeId;

      // Place stop-loss and take-profit orders
      await this.placeRiskManagementOrders(trade);

      return trade;
    } catch (error) {
      this.logger.error('Failed to execute trade', {
        decision,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  }

  /**
   * Close an existing position
   */
  private async closePosition(decision: TradingDecision): Promise<TradeRecord | null> {
    const { symbol, reasoning } = decision;

    this.logger.info('Closing position', { symbol, reasoning });

    try {
      // Close position on exchange
      const closeResult = await this.exchange.closePosition(symbol);

      this.logger.info('Position closed successfully', {
        orderId: closeResult.orderId,
        averagePrice: closeResult.averagePrice,
      });

      // Get open trades for this symbol from database
      const openTrades = await this.database.getTrades({
        symbol,
        status: 'open',
        limit: 1,
      });

      if (openTrades.length === 0) {
        this.logger.warn('No open trade found to close', { symbol });
        return null;
      }

      const openTrade = openTrades[0];

      // Calculate PnL
      const pnl = this.calculatePnL(
        openTrade.entryPrice,
        closeResult.averagePrice,
        openTrade.quantity,
        openTrade.side,
        openTrade.leverage
      );

      const pnlPercent = (pnl / (openTrade.entryPrice * openTrade.quantity / openTrade.leverage)) * 100;

      // Update trade in database
      await this.database.updateTradeStatus(openTrade.id!, 'closed', {
        exitPrice: closeResult.averagePrice,
        pnl,
        pnlPercent,
        closeReason: reasoning,
        duration: Date.now() - openTrade.timestamp,
      });

      // Return updated trade
      return {
        ...openTrade,
        exitPrice: closeResult.averagePrice,
        pnl,
        pnlPercent,
        status: 'closed',
        closeReason: reasoning,
        duration: Date.now() - openTrade.timestamp,
      };
    } catch (error) {
      this.logger.error('Failed to close position', {
        symbol,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      throw error;
    }
  }

  /**
   * Place stop-loss and take-profit orders
   */
  private async placeRiskManagementOrders(trade: TradeRecord): Promise<void> {
    const { symbol, entryPrice, exitPlan, side } = trade;

    try {
      // Calculate stop-loss and take-profit prices
      const stopLossPrice = side === 'buy'
        ? entryPrice * (1 - exitPlan.stopLoss / 100)
        : entryPrice * (1 + exitPlan.stopLoss / 100);

      const takeProfitPrice = side === 'buy'
        ? entryPrice * (1 + exitPlan.takeProfit / 100)
        : entryPrice * (1 - exitPlan.takeProfit / 100);

      this.logger.info('Placing risk management orders', {
        symbol,
        stopLossPrice: stopLossPrice.toFixed(2),
        takeProfitPrice: takeProfitPrice.toFixed(2),
      });

      // In production, place actual stop-loss and take-profit orders
      // await this.exchange.placeOrder({
      //   symbol,
      //   side: side === 'buy' ? 'sell' : 'buy',
      //   type: 'stop_market',
      //   quantity: trade.quantity,
      //   stopPrice: stopLossPrice,
      // });

      // await this.exchange.placeOrder({
      //   symbol,
      //   side: side === 'buy' ? 'sell' : 'buy',
      //   type: 'limit',
      //   quantity: trade.quantity,
      //   price: takeProfitPrice,
      // });

      // For now, just log
      this.logger.debug('Risk management orders would be placed here in production');
    } catch (error) {
      this.logger.error('Failed to place risk management orders', {
        trade,
        error: error instanceof Error ? error.message : 'Unknown error',
      });
      // Don't throw - the main position is already open
    }
  }

  /**
   * Calculate PnL for a trade
   */
  private calculatePnL(
    entryPrice: number,
    exitPrice: number,
    quantity: number,
    side: OrderSide,
    leverage: number
  ): number {
    const priceChange = side === 'buy'
      ? (exitPrice - entryPrice)
      : (entryPrice - exitPrice);

    const grossPnl = priceChange * quantity;
    const leveragedPnl = grossPnl * leverage;

    // Subtract trading fees (0.05% on entry + 0.05% on exit)
    const fees = (entryPrice * quantity * 0.0005) + (exitPrice * quantity * 0.0005);

    return leveragedPnl - fees;
  }

  /**
   * Monitor existing positions and check exit conditions
   */
  async monitorPositions(marketState: MarketState): Promise<void> {
    const { positions } = marketState.account;

    for (const position of positions) {
      await this.checkExitConditions(position, marketState);
    }
  }

  /**
   * Check if position should be exited based on exit plan
   */
  private async checkExitConditions(
    position: any,
    marketState: MarketState
  ): Promise<void> {
    // Get the trade record from database
    const trades = await this.database.getTrades({
      symbol: position.symbol,
      status: 'open',
      limit: 1,
    });

    if (trades.length === 0) {
      return;
    }

    const trade = trades[0];
    const currentPrice = marketState.pairs[position.symbol]?.price;

    if (!currentPrice) {
      return;
    }

    // Check stop-loss
    const stopLossPrice = trade.side === 'buy'
      ? trade.entryPrice * (1 - trade.exitPlan.stopLoss / 100)
      : trade.entryPrice * (1 + trade.exitPlan.stopLoss / 100);

    const hitStopLoss = trade.side === 'buy'
      ? currentPrice <= stopLossPrice
      : currentPrice >= stopLossPrice;

    if (hitStopLoss) {
      this.logger.warn('Stop-loss triggered', {
        symbol: trade.symbol,
        currentPrice,
        stopLossPrice,
      });

      await this.closePosition({
        action: 'CLOSE',
        symbol: trade.symbol,
        quantity: 0,
        leverage: 1,
        confidence: 1,
        reasoning: 'Stop-loss triggered',
        exitPlan: trade.exitPlan,
      });
      return;
    }

    // Check take-profit
    const takeProfitPrice = trade.side === 'buy'
      ? trade.entryPrice * (1 + trade.exitPlan.takeProfit / 100)
      : trade.entryPrice * (1 - trade.exitPlan.takeProfit / 100);

    const hitTakeProfit = trade.side === 'buy'
      ? currentPrice >= takeProfitPrice
      : currentPrice <= takeProfitPrice;

    if (hitTakeProfit) {
      this.logger.info('Take-profit triggered', {
        symbol: trade.symbol,
        currentPrice,
        takeProfitPrice,
      });

      await this.closePosition({
        action: 'CLOSE',
        symbol: trade.symbol,
        quantity: 0,
        leverage: 1,
        confidence: 1,
        reasoning: 'Take-profit target reached',
        exitPlan: trade.exitPlan,
      });
    }
  }
}
