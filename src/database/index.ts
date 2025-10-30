/**
 * Database layer using SQLite
 */

import Database from 'better-sqlite3';
import { mkdir } from 'fs/promises';
import { dirname } from 'path';
import type {
  IDatabase,
  TradeRecord,
  DecisionRecord,
  PerformanceMetrics,
  TradeFilter,
  DecisionFilter,
} from '../types/index.js';

export class TradingDatabase implements IDatabase {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.initializeTables();
  }

  /**
   * Create database tables if they don't exist
   */
  private initializeTables(): void {
    // Trades table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        action TEXT NOT NULL,
        side TEXT NOT NULL,
        quantity REAL NOT NULL,
        entry_price REAL NOT NULL,
        exit_price REAL,
        leverage INTEGER NOT NULL,
        pnl REAL,
        pnl_percent REAL,
        confidence REAL NOT NULL,
        reasoning TEXT NOT NULL,
        exit_plan TEXT NOT NULL,
        status TEXT NOT NULL,
        close_reason TEXT,
        duration INTEGER,
        created_at INTEGER DEFAULT (strftime('%s', 'now'))
      );
    `);

    // Decisions table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        market_state TEXT NOT NULL,
        ai_output TEXT NOT NULL,
        risk_approved INTEGER NOT NULL,
        rejection_reason TEXT,
        execution_time INTEGER,
        created_at INTEGER DEFAULT (strftime('%s', 'now'))
      );
    `);

    // Performance metrics table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER NOT NULL,
        total_pnl REAL NOT NULL,
        total_pnl_percent REAL NOT NULL,
        sharpe_ratio REAL NOT NULL,
        win_rate REAL NOT NULL,
        total_trades INTEGER NOT NULL,
        winning_trades INTEGER NOT NULL,
        losing_trades INTEGER NOT NULL,
        average_win REAL NOT NULL,
        average_loss REAL NOT NULL,
        profit_factor REAL NOT NULL,
        max_drawdown REAL NOT NULL,
        max_drawdown_percent REAL NOT NULL,
        current_equity REAL NOT NULL,
        daily_pnl REAL NOT NULL,
        daily_pnl_percent REAL NOT NULL,
        created_at INTEGER DEFAULT (strftime('%s', 'now'))
      );
    `);

    // Create indexes for faster queries
    this.db.exec(`
      CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
      CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
      CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
      CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp);
      CREATE INDEX IF NOT EXISTS idx_decisions_approved ON decisions(risk_approved);
      CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance(timestamp);
    `);
  }

  /**
   * Save a trade record
   */
  async saveTrade(trade: TradeRecord): Promise<number> {
    const stmt = this.db.prepare(`
      INSERT INTO trades (
        timestamp, symbol, action, side, quantity, entry_price, exit_price,
        leverage, pnl, pnl_percent, confidence, reasoning, exit_plan,
        status, close_reason, duration
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const result = stmt.run(
      trade.timestamp,
      trade.symbol,
      trade.action,
      trade.side,
      trade.quantity,
      trade.entryPrice,
      trade.exitPrice ?? null,
      trade.leverage,
      trade.pnl ?? null,
      trade.pnlPercent ?? null,
      trade.confidence,
      trade.reasoning,
      JSON.stringify(trade.exitPlan),
      trade.status,
      trade.closeReason ?? null,
      trade.duration ?? null
    );

    return result.lastInsertRowid as number;
  }

  /**
   * Save a decision record
   */
  async saveDecision(decision: DecisionRecord): Promise<number> {
    const stmt = this.db.prepare(`
      INSERT INTO decisions (
        timestamp, market_state, ai_output, risk_approved, rejection_reason, execution_time
      ) VALUES (?, ?, ?, ?, ?, ?)
    `);

    const result = stmt.run(
      decision.timestamp,
      decision.marketState,
      decision.aiOutput,
      decision.riskApproved ? 1 : 0,
      decision.rejectionReason ?? null,
      decision.executionTime ?? null
    );

    return result.lastInsertRowid as number;
  }

  /**
   * Save performance metrics
   */
  async savePerformance(metrics: PerformanceMetrics): Promise<void> {
    const stmt = this.db.prepare(`
      INSERT INTO performance (
        timestamp, total_pnl, total_pnl_percent, sharpe_ratio, win_rate,
        total_trades, winning_trades, losing_trades, average_win, average_loss,
        profit_factor, max_drawdown, max_drawdown_percent, current_equity,
        daily_pnl, daily_pnl_percent
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      metrics.timestamp,
      metrics.totalPnl,
      metrics.totalPnlPercent,
      metrics.sharpeRatio,
      metrics.winRate,
      metrics.totalTrades,
      metrics.winningTrades,
      metrics.losingTrades,
      metrics.averageWin,
      metrics.averageLoss,
      metrics.profitFactor,
      metrics.maxDrawdown,
      metrics.maxDrawdownPercent,
      metrics.currentEquity,
      metrics.dailyPnl,
      metrics.dailyPnlPercent
    );
  }

  /**
   * Get trades with optional filtering
   */
  async getTrades(filter?: TradeFilter): Promise<TradeRecord[]> {
    let query = 'SELECT * FROM trades WHERE 1=1';
    const params: unknown[] = [];

    if (filter?.symbol) {
      query += ' AND symbol = ?';
      params.push(filter.symbol);
    }

    if (filter?.status) {
      query += ' AND status = ?';
      params.push(filter.status);
    }

    if (filter?.fromTimestamp) {
      query += ' AND timestamp >= ?';
      params.push(filter.fromTimestamp);
    }

    if (filter?.toTimestamp) {
      query += ' AND timestamp <= ?';
      params.push(filter.toTimestamp);
    }

    query += ' ORDER BY timestamp DESC';

    if (filter?.limit) {
      query += ' LIMIT ?';
      params.push(filter.limit);
    }

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as any[];

    return rows.map(row => ({
      id: row.id,
      timestamp: row.timestamp,
      symbol: row.symbol,
      action: row.action,
      side: row.side,
      quantity: row.quantity,
      entryPrice: row.entry_price,
      exitPrice: row.exit_price,
      leverage: row.leverage,
      pnl: row.pnl,
      pnlPercent: row.pnl_percent,
      confidence: row.confidence,
      reasoning: row.reasoning,
      exitPlan: JSON.parse(row.exit_plan),
      status: row.status,
      closeReason: row.close_reason,
      duration: row.duration,
    }));
  }

  /**
   * Get decisions with optional filtering
   */
  async getDecisions(filter?: DecisionFilter): Promise<DecisionRecord[]> {
    let query = 'SELECT * FROM decisions WHERE 1=1';
    const params: unknown[] = [];

    if (filter?.riskApproved !== undefined) {
      query += ' AND risk_approved = ?';
      params.push(filter.riskApproved ? 1 : 0);
    }

    if (filter?.fromTimestamp) {
      query += ' AND timestamp >= ?';
      params.push(filter.fromTimestamp);
    }

    if (filter?.toTimestamp) {
      query += ' AND timestamp <= ?';
      params.push(filter.toTimestamp);
    }

    query += ' ORDER BY timestamp DESC';

    if (filter?.limit) {
      query += ' LIMIT ?';
      params.push(filter.limit);
    }

    const stmt = this.db.prepare(query);
    const rows = stmt.all(...params) as any[];

    return rows.map(row => ({
      id: row.id,
      timestamp: row.timestamp,
      marketState: row.market_state,
      aiOutput: row.ai_output,
      riskApproved: row.risk_approved === 1,
      rejectionReason: row.rejection_reason,
      executionTime: row.execution_time,
    }));
  }

  /**
   * Get latest performance metrics
   */
  async getLatestPerformance(): Promise<PerformanceMetrics | null> {
    const stmt = this.db.prepare(`
      SELECT * FROM performance ORDER BY timestamp DESC LIMIT 1
    `);

    const row = stmt.get() as any;

    if (!row) {
      return null;
    }

    return {
      timestamp: row.timestamp,
      totalPnl: row.total_pnl,
      totalPnlPercent: row.total_pnl_percent,
      sharpeRatio: row.sharpe_ratio,
      winRate: row.win_rate,
      totalTrades: row.total_trades,
      winningTrades: row.winning_trades,
      losingTrades: row.losing_trades,
      averageWin: row.average_win,
      averageLoss: row.average_loss,
      profitFactor: row.profit_factor,
      maxDrawdown: row.max_drawdown,
      maxDrawdownPercent: row.max_drawdown_percent,
      currentEquity: row.current_equity,
      dailyPnl: row.daily_pnl,
      dailyPnlPercent: row.daily_pnl_percent,
    };
  }

  /**
   * Update trade status and exit data
   */
  async updateTradeStatus(
    tradeId: number,
    status: TradeRecord['status'],
    exitData?: Partial<TradeRecord>
  ): Promise<void> {
    const updates: string[] = ['status = ?'];
    const params: unknown[] = [status];

    if (exitData?.exitPrice !== undefined) {
      updates.push('exit_price = ?');
      params.push(exitData.exitPrice);
    }

    if (exitData?.pnl !== undefined) {
      updates.push('pnl = ?');
      params.push(exitData.pnl);
    }

    if (exitData?.pnlPercent !== undefined) {
      updates.push('pnl_percent = ?');
      params.push(exitData.pnlPercent);
    }

    if (exitData?.closeReason) {
      updates.push('close_reason = ?');
      params.push(exitData.closeReason);
    }

    if (exitData?.duration !== undefined) {
      updates.push('duration = ?');
      params.push(exitData.duration);
    }

    params.push(tradeId);

    const stmt = this.db.prepare(`
      UPDATE trades SET ${updates.join(', ')} WHERE id = ?
    `);

    stmt.run(...params);
  }

  /**
   * Close database connection
   */
  close(): void {
    this.db.close();
  }
}

/**
 * Initialize database with directory creation
 */
export async function initDatabase(dbPath: string): Promise<TradingDatabase> {
  // Ensure database directory exists
  await mkdir(dirname(dbPath), { recursive: true });
  return new TradingDatabase(dbPath);
}
