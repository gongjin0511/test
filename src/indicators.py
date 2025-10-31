"""
Technical indicators calculator
"""

import numpy as np
import pandas as pd
from typing import List, Optional
from .types import OHLCV, TechnicalIndicators


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))


def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return None

    df = pd.DataFrame({'price': prices})
    ema = df['price'].ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1])


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return None

    df = pd.DataFrame({'price': prices})
    delta = df['price'].diff()

    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi.iloc[-1])


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Optional[dict]:
    """Calculate MACD"""
    if len(prices) < slow_period:
        return None

    df = pd.DataFrame({'price': prices})

    fast_ema = df['price'].ewm(span=fast_period, adjust=False).mean()
    slow_ema = df['price'].ewm(span=slow_period, adjust=False).mean()

    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        'macd': float(macd_line.iloc[-1]),
        'signal': float(signal_line.iloc[-1]),
        'histogram': float(histogram.iloc[-1])
    }


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Optional[dict]:
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return None

    df = pd.DataFrame({'price': prices})

    sma = df['price'].rolling(window=period).mean()
    std = df['price'].rolling(window=period).std()

    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)

    return {
        'upper': float(upper.iloc[-1]),
        'middle': float(sma.iloc[-1]),
        'lower': float(lower.iloc[-1])
    }


def calculate_atr(candles: List[OHLCV], period: int = 14) -> Optional[float]:
    """Calculate Average True Range"""
    if len(candles) < period + 1:
        return None

    true_ranges = []
    for i in range(1, len(candles)):
        high_low = candles[i].high - candles[i].low
        high_close = abs(candles[i].high - candles[i-1].close)
        low_close = abs(candles[i].low - candles[i-1].close)

        true_ranges.append(max(high_low, high_close, low_close))

    return float(np.mean(true_ranges[-period:]))


def calculate_all_indicators(
    close_prices: List[float],
    candles: Optional[List[OHLCV]] = None
) -> TechnicalIndicators:
    """Calculate all technical indicators"""

    indicators = TechnicalIndicators(
        sma20=calculate_sma(close_prices, 20),
        sma50=calculate_sma(close_prices, 50),
        ema12=calculate_ema(close_prices, 12),
        ema26=calculate_ema(close_prices, 26),
        rsi=calculate_rsi(close_prices, 14),
        macd=calculate_macd(close_prices),
        bollinger_bands=calculate_bollinger_bands(close_prices, 20, 2)
    )

    if candles and len(candles) > 0:
        indicators.atr = calculate_atr(candles, 14)

    return indicators
