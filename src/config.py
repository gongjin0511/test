"""
Configuration loader with validation
"""

import os
from typing import Optional
from dotenv import load_dotenv
from .types import SystemConfig, OKXConfig, AIConfig, TradingConfig, RiskConfig, DatabaseConfig, LoggingConfig, RedisConfig

# Load environment variables
load_dotenv()


def parse_trading_pairs(pairs_str: Optional[str]) -> list[str]:
    """Parse comma-separated trading pairs"""
    if not pairs_str:
        return ['BTC-USDT-SWAP', 'ETH-USDT-SWAP', 'SOL-USDT-SWAP']
    return [pair.strip() for pair in pairs_str.split(',') if pair.strip()]


def load_config() -> SystemConfig:
    """Load and validate system configuration from environment variables"""

    okx_config = OKXConfig(
        api_key=os.getenv('OKX_API_KEY', ''),
        secret_key=os.getenv('OKX_SECRET_KEY', ''),
        passphrase=os.getenv('OKX_PASSPHRASE', ''),
        environment=os.getenv('OKX_API_ENV', 'demo'),
        testnet=os.getenv('OKX_API_ENV', 'demo') == 'demo'
    )

    ai_provider = os.getenv('AI_PROVIDER', 'anthropic')
    ai_config = AIConfig(
        provider=ai_provider,
        api_key=os.getenv('ANTHROPIC_API_KEY' if ai_provider == 'anthropic' else 'OPENAI_API_KEY', ''),
        model=os.getenv('AI_MODEL', 'claude-sonnet-4.5'),
        temperature=float(os.getenv('AI_TEMPERATURE', '0.7')),
        max_tokens=int(os.getenv('AI_MAX_TOKENS', '4000')),
        custom_endpoint=os.getenv('AI_CUSTOM_ENDPOINT')
    )

    trading_config = TradingConfig(
        initial_capital=float(os.getenv('INITIAL_CAPITAL', '10000')),
        trading_pairs=parse_trading_pairs(os.getenv('TRADING_PAIRS')),
        decision_interval_ms=int(os.getenv('DECISION_INTERVAL_MS', '180000')),
        mode=os.getenv('TRADING_MODE', 'testnet'),
        max_leverage=int(os.getenv('MAX_LEVERAGE', '5')),
        max_position_size_percent=float(os.getenv('MAX_POSITION_SIZE_PERCENTAGE', '20')),
        stop_loss_percent=float(os.getenv('STOP_LOSS_PERCENTAGE', '5')),
        take_profit_percent=float(os.getenv('TAKE_PROFIT_PERCENTAGE', '10')),
        max_concurrent_positions=int(os.getenv('MAX_CONCURRENT_POSITIONS', '3')),
        enable_short_selling=os.getenv('ENABLE_SHORT_SELLING', 'true').lower() != 'false'
    )

    risk_config = RiskConfig(
        max_daily_loss_percent=float(os.getenv('MAX_DAILY_LOSS_PERCENT', '10')),
        max_drawdown_percent=float(os.getenv('MAX_DRAWDOWN_PERCENT', '20')),
        max_portfolio_exposure_percent=float(os.getenv('MAX_PORTFOLIO_EXPOSURE_PERCENT', '80')),
        require_stop_loss=os.getenv('REQUIRE_STOP_LOSS', 'true').lower() != 'false',
        min_confidence_threshold=float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.6')),
        circuit_breaker_enabled=os.getenv('CIRCUIT_BREAKER_ENABLED', 'true').lower() != 'false'
    )

    database_config = DatabaseConfig(
        path=os.getenv('DB_PATH', './data/trading.db')
    )

    logging_config = LoggingConfig(
        level=os.getenv('LOG_LEVEL', 'info'),
        file_path=os.getenv('LOG_FILE', './logs/trading.log')
    )

    redis_config = None
    if os.getenv('REDIS_ENABLED', 'false').lower() == 'true':
        redis_config = RedisConfig(
            url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
            enabled=True
        )

    return SystemConfig(
        okx=okx_config,
        ai=ai_config,
        trading=trading_config,
        risk=risk_config,
        database=database_config,
        logging=logging_config,
        redis=redis_config
    )


# Cached config instance
_cached_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get configuration with caching"""
    global _cached_config
    if _cached_config is None:
        _cached_config = load_config()
    return _cached_config


def validate_config() -> tuple[bool, Optional[list[str]]]:
    """Validate configuration without throwing"""
    try:
        load_config()
        return True, None
    except Exception as e:
        return False, [str(e)]
