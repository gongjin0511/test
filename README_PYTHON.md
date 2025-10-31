# OKX AI Trading System - Python Edition

Python implementation of the autonomous AI-powered cryptocurrency trading system for OKX exchange, inspired by nof1.ai's Alpha Arena.

## 🐍 Why Python?

This Python version offers:
- **Faster development**: Python's simplicity and rich ecosystem
- **Data science integration**: Easy integration with pandas, numpy, scikit-learn
- **CCXT library**: Unified exchange API access
- **Async/await**: Modern asynchronous programming
- **Type hints**: Type safety with Pydantic models

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OKX account with API keys
- Anthropic API key (for Claude)

### Installation

```bash
# Clone repository and navigate to python-dev branch
git clone <repo-url>
git checkout python-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required environment variables:
```bash
# OKX API
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
OKX_API_ENV=demo  # or 'production'

# AI
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key
AI_MODEL=claude-sonnet-4.5

# Trading
INITIAL_CAPITAL=10000
TRADING_MODE=testnet
TRADING_PAIRS=BTC-USDT-SWAP,ETH-USDT-SWAP,SOL-USDT-SWAP
```

### Run

```bash
# Run the trading system
python -m src.main

# Or with uvloop for better performance
pip install uvloop
python -m src.main
```

## 📁 Project Structure

```
src/
├── __init__.py              # Package initialization
├── types.py                 # Type definitions (Pydantic models)
├── config.py                # Configuration loader
├── database.py              # SQLite database layer
├── exchange_client.py       # OKX exchange client (CCXT)
├── indicators.py            # Technical indicators calculator
├── ai_provider.py           # Anthropic AI provider
├── risk_manager.py          # Risk management system
├── orchestrator.py          # Main trading orchestrator
├── prompts.py               # System prompts
└── main.py                  # Entry point
```

## 🔑 Key Features

### Type Safety with Pydantic

```python
class TradingDecision(BaseModel):
    action: TradingAction
    symbol: str
    quantity: float
    leverage: int = Field(ge=1, le=125)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    exit_plan: ExitPlan
```

### Async/Await Support

```python
async def get_market_data(symbol: str) -> MarketSnapshot:
    ticker = await exchange.fetch_ticker(symbol)
    candles = await exchange.fetch_ohlcv(symbol, '1m', limit=100)
    return MarketSnapshot(...)
```

### CCXT Exchange Integration

```python
# Unified API for multiple exchanges
exchange = ccxt.okx({
    'apiKey': api_key,
    'secret': secret_key,
    'password': passphrase,
})

# Easy to switch to other exchanges
# exchange = ccxt.binance({...})
```

### Technical Indicators with Pandas/NumPy

```python
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    df = pd.DataFrame({'price': prices})
    delta = df['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])
```

## 🆚 Comparison: Python vs TypeScript

| Feature | Python | TypeScript |
|---------|--------|------------|
| Development Speed | ⚡⚡⚡ Faster | ⚡⚡ Moderate |
| Type Safety | ✅ Pydantic | ✅ Native |
| Exchange API | ccxt (unified) | okx-api (specific) |
| Data Analysis | pandas, numpy | Limited |
| Performance | ⚡⚡ Good | ⚡⚡⚡ Better |
| Deployment | Python runtime | Node.js runtime |
| Community | Huge (trading/ML) | Large (web dev) |

## 📚 Libraries Used

- **anthropic**: Anthropic Claude API client
- **ccxt**: Cryptocurrency exchange trading library
- **pydantic**: Data validation using Python type hints
- **python-dotenv**: Environment variable management
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **ta**: Technical analysis indicators (alternative)

## 🔧 Development

### Run Tests

```bash
pytest tests/
```

### Code Formatting

```bash
# Format code with Black
black src/

# Lint with flake8
flake8 src/

# Type checking with mypy
mypy src/
```

### Add New Features

1. Define types in `types.py` using Pydantic
2. Implement logic in appropriate module
3. Update orchestrator if needed
4. Add tests

## 🐛 Debugging

### Enable Debug Logging

```bash
LOG_LEVEL=debug python -m src.main
```

### Interactive REPL

```python
# In Python REPL
from src.config import get_config
from src.database import init_database

config = get_config()
db = init_database(config.database.path)

# Query trades
trades = db.get_trades(limit=10)
for trade in trades:
    print(f"{trade.symbol}: {trade.pnl}")
```

### Database Inspection

```bash
# SQLite CLI
sqlite3 data/trading.db

# List recent trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

# Check performance
SELECT * FROM performance ORDER BY timestamp DESC LIMIT 1;
```

## 🚀 Production Deployment

### Using systemd (Linux)

```bash
# Create service file
sudo nano /etc/systemd/system/okx-trading.service
```

```ini
[Unit]
Description=OKX AI Trading System
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m src.main
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable okx-trading
sudo systemctl start okx-trading

# Check status
sudo systemctl status okx-trading

# View logs
sudo journalctl -u okx-trading -f
```

### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .

CMD ["python", "-m", "src.main"]
```

```bash
# Build and run
docker build -t okx-trading .
docker run -d --name okx-trading --env-file .env okx-trading
```

## 📊 Monitoring

### View System Status

```python
# In running system, check orchestrator state
print(orchestrator.is_running)

# Get recent performance
performance = database.get_latest_performance()
print(f"Total PnL: ${performance.total_pnl:.2f}")
print(f"Win Rate: {performance.win_rate:.1f}%")
```

### Log Analysis

```bash
# View logs
tail -f logs/trading.log

# Filter errors
grep ERROR logs/trading.log

# Count decisions
grep "AI decision generated" logs/trading.log | wc -l
```

## 🔮 Future Enhancements

- [ ] Memory system (port from TypeScript version)
- [ ] Post-trade analysis
- [ ] Multi-agent competition
- [ ] Backtesting engine
- [ ] Web dashboard (FastAPI + React)
- [ ] Machine learning integration (scikit-learn)
- [ ] Additional exchanges (Binance, Coinbase)
- [ ] Real-time monitoring with Prometheus/Grafana

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Memory and learning system
- Advanced indicators
- Better error handling
- Performance optimization
- Documentation improvements

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- Inspired by [nof1.ai's Alpha Arena](https://nof1.ai/)
- Built with [Anthropic Claude](https://www.anthropic.com/)
- Powered by [CCXT](https://github.com/ccxt/ccxt)

---

**Disclaimer**: Cryptocurrency trading is risky. This software is for educational purposes. Trade responsibly and never risk more than you can afford to lose.
