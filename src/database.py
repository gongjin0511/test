"""
Database layer using SQLite
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Optional, List
from .types import TradeRecord, DecisionRecord, PerformanceMetrics, TradingAction, OrderSide


class TradingDatabase:
    """SQLite database for trading system"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._initialize_tables()

    def _initialize_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Trades table
        cursor.execute("""
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
            )
        """)

        # Decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                market_state TEXT NOT NULL,
                ai_output TEXT NOT NULL,
                risk_approved INTEGER NOT NULL,
                rejection_reason TEXT,
                execution_time INTEGER,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        """)

        # Performance metrics table
        cursor.execute("""
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
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_approved ON decisions(risk_approved)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance(timestamp)")

        self.conn.commit()

    def save_trade(self, trade: TradeRecord) -> int:
        """Save a trade record"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO trades (
                timestamp, symbol, action, side, quantity, entry_price, exit_price,
                leverage, pnl, pnl_percent, confidence, reasoning, exit_plan,
                status, close_reason, duration
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.timestamp,
            trade.symbol,
            trade.action.value,
            trade.side.value,
            trade.quantity,
            trade.entry_price,
            trade.exit_price,
            trade.leverage,
            trade.pnl,
            trade.pnl_percent,
            trade.confidence,
            trade.reasoning,
            json.dumps(trade.exit_plan.model_dump()),
            trade.status,
            trade.close_reason,
            trade.duration
        ))
        self.conn.commit()
        return cursor.lastrowid

    def save_decision(self, decision: DecisionRecord) -> int:
        """Save a decision record"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO decisions (
                timestamp, market_state, ai_output, risk_approved, rejection_reason, execution_time
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            decision.timestamp,
            decision.market_state,
            decision.ai_output,
            1 if decision.risk_approved else 0,
            decision.rejection_reason,
            decision.execution_time
        ))
        self.conn.commit()
        return cursor.lastrowid

    def save_performance(self, metrics: PerformanceMetrics):
        """Save performance metrics"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO performance (
                timestamp, total_pnl, total_pnl_percent, sharpe_ratio, win_rate,
                total_trades, winning_trades, losing_trades, average_win, average_loss,
                profit_factor, max_drawdown, max_drawdown_percent, current_equity,
                daily_pnl, daily_pnl_percent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.timestamp, metrics.total_pnl, metrics.total_pnl_percent,
            metrics.sharpe_ratio, metrics.win_rate, metrics.total_trades,
            metrics.winning_trades, metrics.losing_trades, metrics.average_win,
            metrics.average_loss, metrics.profit_factor, metrics.max_drawdown,
            metrics.max_drawdown_percent, metrics.current_equity,
            metrics.daily_pnl, metrics.daily_pnl_percent
        ))
        self.conn.commit()

    def get_trades(
        self,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[TradeRecord]:
        """Get trades with optional filtering"""
        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if status:
            query += " AND status = ?"
            params.append(status)
        if from_timestamp:
            query += " AND timestamp >= ?"
            params.append(from_timestamp)
        if to_timestamp:
            query += " AND timestamp <= ?"
            params.append(to_timestamp)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        trades = []
        for row in cursor.fetchall():
            trades.append(TradeRecord(
                id=row['id'],
                timestamp=row['timestamp'],
                symbol=row['symbol'],
                action=TradingAction(row['action']),
                side=OrderSide(row['side']),
                quantity=row['quantity'],
                entry_price=row['entry_price'],
                exit_price=row['exit_price'],
                leverage=row['leverage'],
                pnl=row['pnl'],
                pnl_percent=row['pnl_percent'],
                confidence=row['confidence'],
                reasoning=row['reasoning'],
                exit_plan=json.loads(row['exit_plan']),
                status=row['status'],
                close_reason=row['close_reason'],
                duration=row['duration']
            ))

        return trades

    def get_latest_performance(self) -> Optional[PerformanceMetrics]:
        """Get latest performance metrics"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM performance ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()

        if not row:
            return None

        return PerformanceMetrics(
            timestamp=row['timestamp'],
            total_pnl=row['total_pnl'],
            total_pnl_percent=row['total_pnl_percent'],
            sharpe_ratio=row['sharpe_ratio'],
            win_rate=row['win_rate'],
            total_trades=row['total_trades'],
            winning_trades=row['winning_trades'],
            losing_trades=row['losing_trades'],
            average_win=row['average_win'],
            average_loss=row['average_loss'],
            profit_factor=row['profit_factor'],
            max_drawdown=row['max_drawdown'],
            max_drawdown_percent=row['max_drawdown_percent'],
            current_equity=row['current_equity'],
            daily_pnl=row['daily_pnl'],
            daily_pnl_percent=row['daily_pnl_percent']
        )

    def update_trade_status(
        self,
        trade_id: int,
        status: str,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None,
        pnl_percent: Optional[float] = None,
        close_reason: Optional[str] = None,
        duration: Optional[int] = None
    ):
        """Update trade status and exit data"""
        updates = ["status = ?"]
        params = [status]

        if exit_price is not None:
            updates.append("exit_price = ?")
            params.append(exit_price)
        if pnl is not None:
            updates.append("pnl = ?")
            params.append(pnl)
        if pnl_percent is not None:
            updates.append("pnl_percent = ?")
            params.append(pnl_percent)
        if close_reason:
            updates.append("close_reason = ?")
            params.append(close_reason)
        if duration is not None:
            updates.append("duration = ?")
            params.append(duration)

        params.append(trade_id)

        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE trades SET {', '.join(updates)} WHERE id = ?", params)
        self.conn.commit()

    def close(self):
        """Close database connection"""
        self.conn.close()


def init_database(db_path: str) -> TradingDatabase:
    """Initialize database with directory creation"""
    return TradingDatabase(db_path)
