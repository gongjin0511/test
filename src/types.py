"""
OKX AI Trading System - Type Definitions
Python implementation with Pydantic models
"""

from enum import Enum
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== Trading Types ====================

class TradingAction(str, Enum):
    OPEN_LONG = "OPEN_LONG"
    OPEN_SHORT = "OPEN_SHORT"
    CLOSE = "CLOSE"
    HOLD = "HOLD"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"
    NET = "net"


class TradingPair(BaseModel):
    symbol: str  # e.g., 'BTC-USDT-SWAP'
    base_currency: str  # e.g., 'BTC'
    quote_currency: str  # e.g., 'USDT'
    contract_type: str  # e.g., 'SWAP' (perpetual)


class ExitPlan(BaseModel):
    take_profit: float  # Target profit percentage
    stop_loss: float  # Stop loss percentage
    invalidation: str  # Conditions to exit early


class TradingDecision(BaseModel):
    action: TradingAction
    symbol: str
    quantity: float
    leverage: int = Field(ge=1, le=125)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    exit_plan: ExitPlan
    self_reflection: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# ==================== Market Data Types ====================

class OHLCV(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class OrderBookLevel(BaseModel):
    price: float
    quantity: float


class OrderBook(BaseModel):
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: int


class TechnicalIndicators(BaseModel):
    sma20: Optional[float] = None
    sma50: Optional[float] = None
    ema12: Optional[float] = None
    ema26: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[Dict[str, float]] = None
    bollinger_bands: Optional[Dict[str, float]] = None
    atr: Optional[float] = None


class MarketSnapshot(BaseModel):
    symbol: str
    price: float
    price_change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    funding_rate: Optional[float] = None
    open_interest: Optional[float] = None
    indicators: TechnicalIndicators
    order_book: Optional[OrderBook] = None
    recent_candles: Optional[List[OHLCV]] = None


class AccountPosition(BaseModel):
    symbol: str
    side: PositionSide
    size: float
    entry_price: float
    current_price: float
    leverage: int
    unrealized_pnl: float
    unrealized_pnl_percent: float
    liquidation_price: Optional[float] = None
    timestamp: int


class AccountState(BaseModel):
    total_equity: float
    available_balance: float
    used_margin: float
    unrealized_pnl: float
    positions: List[AccountPosition]
    open_orders_count: int


class MarketState(BaseModel):
    timestamp: int
    pairs: Dict[str, MarketSnapshot]
    account: AccountState
    performance_metrics: Optional['PerformanceMetrics'] = None


# ==================== Performance & Risk Types ====================

class TradeRecord(BaseModel):
    id: Optional[int] = None
    timestamp: int
    symbol: str
    action: TradingAction
    side: OrderSide
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    leverage: int
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    confidence: float
    reasoning: str
    exit_plan: ExitPlan
    status: str  # 'open', 'closed', 'cancelled'
    close_reason: Optional[str] = None
    duration: Optional[int] = None  # In milliseconds


class DecisionRecord(BaseModel):
    id: Optional[int] = None
    timestamp: int
    market_state: str  # JSON stringified
    ai_output: str  # JSON stringified
    risk_approved: bool
    rejection_reason: Optional[str] = None
    execution_time: Optional[int] = None


class PerformanceMetrics(BaseModel):
    timestamp: int
    total_pnl: float
    total_pnl_percent: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_percent: float
    current_equity: float
    daily_pnl: float
    daily_pnl_percent: float


class RiskMetrics(BaseModel):
    current_exposure: float
    exposure_percent: float
    max_single_position_size: float
    portfolio_leverage: float
    available_risk_capital: float
    correlation_risk: Optional[float] = None


# ==================== Configuration Types ====================

class OKXConfig(BaseModel):
    api_key: str
    secret_key: str
    passphrase: str
    environment: str = Field(pattern='^(demo|production)$')
    testnet: bool = False


class AIConfig(BaseModel):
    provider: str = Field(pattern='^(anthropic|openai|custom)$')
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    custom_endpoint: Optional[str] = None


class TradingConfig(BaseModel):
    initial_capital: float
    trading_pairs: List[str]
    decision_interval_ms: int
    mode: str = Field(pattern='^(testnet|live)$')
    max_leverage: int = Field(ge=1, le=125)
    max_position_size_percent: float = Field(ge=1, le=100)
    stop_loss_percent: float
    take_profit_percent: float
    max_concurrent_positions: int
    enable_short_selling: bool


class RiskConfig(BaseModel):
    max_daily_loss_percent: float
    max_drawdown_percent: float
    max_portfolio_exposure_percent: float = Field(ge=1, le=100)
    require_stop_loss: bool
    min_confidence_threshold: float = Field(ge=0, le=1)
    circuit_breaker_enabled: bool


class DatabaseConfig(BaseModel):
    path: str


class LoggingConfig(BaseModel):
    level: str = Field(pattern='^(debug|info|warn|error)$')
    file_path: str


class RedisConfig(BaseModel):
    url: str
    enabled: bool


class SystemConfig(BaseModel):
    okx: OKXConfig
    ai: AIConfig
    trading: TradingConfig
    risk: RiskConfig
    database: DatabaseConfig
    logging: LoggingConfig
    redis: Optional[RedisConfig] = None


# ==================== Memory Types ====================

class Lesson(BaseModel):
    id: Optional[int] = None
    timestamp: int
    category: str  # 'success', 'failure', 'insight'
    content: str
    context: str
    importance: int = Field(ge=1, le=10)
    application_count: int = 0


class Pattern(BaseModel):
    id: Optional[int] = None
    description: str
    indicators: Dict[str, Any]
    outcome: str  # 'positive', 'negative'
    frequency: int
    avg_return: float
    confidence: float


class MarketRegime(BaseModel):
    id: Optional[int] = None
    name: str
    characteristics: str
    performance: float
    trade_count: int
    last_seen: int


class PersonalityTraits(BaseModel):
    risk_tolerance: float = Field(ge=0, le=1)
    aggressiveness: float = Field(ge=0, le=1)
    patience: float = Field(ge=0, le=1)
    adaptability: float = Field(ge=0, le=1)
    confidence_level: float = Field(ge=0, le=1)
    trading_philosophy: str


class ShortTermMemory(BaseModel):
    recent_trades: List[TradeRecord]
    recent_decisions: List[str]
    current_streak: Dict[str, Any]
    recent_market_conditions: List[str]


class LongTermMemory(BaseModel):
    key_lessons: List[Lesson]
    success_patterns: List[Pattern]
    failure_patterns: List[Pattern]
    market_regimes: List[MarketRegime]
    personality_traits: PersonalityTraits


# ==================== Order Types ====================

class OrderParams(BaseModel):
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None
    leverage: Optional[int] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_side: Optional[PositionSide] = None


class OrderResult(BaseModel):
    order_id: str
    symbol: str
    status: str
    filled_quantity: float
    average_price: float
    timestamp: int
    fee: Optional[float] = None


class RiskValidationResult(BaseModel):
    approved: bool
    reason: Optional[str] = None
    adjusted_decision: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None


# ==================== Error Types ====================

class TradingError(Exception):
    """Base trading error"""
    def __init__(self, message: str, code: str, details: Any = None):
        self.message = message
        self.code = code
        self.details = details
        super().__init__(self.message)


class ExchangeError(TradingError):
    """Exchange-related error"""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message, 'EXCHANGE_ERROR', details)


class RiskViolationError(TradingError):
    """Risk management violation"""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message, 'RISK_VIOLATION', details)


class AIProviderError(TradingError):
    """AI provider error"""
    def __init__(self, message: str, details: Any = None):
        super().__init__(message, 'AI_PROVIDER_ERROR', details)
