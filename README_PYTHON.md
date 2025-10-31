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
├── __init__.py                  # Package initialization
├── types.py                     # Type definitions (Pydantic models)
├── config.py                    # Configuration loader
├── database.py                  # SQLite database layer
├── exchange_client.py           # OKX exchange client (CCXT)
├── indicators.py                # Technical indicators calculator
├── ai_provider.py               # Base Anthropic AI provider
├── ai_provider_enhanced.py      # ✨ Enhanced AI with memory integration
├── risk_manager.py              # Risk management system
├── orchestrator.py              # Base trading orchestrator
├── orchestrator_enhanced.py     # ✨ Enhanced orchestrator with learning
├── memory_system.py             # ✨ Dual-layer memory system
├── post_trade_analysis.py       # ✨ Trade analysis and learning
├── dynamic_prompt.py            # ✨ Dynamic prompt evolution
├── backtesting.py               # ✨ LLM-powered backtesting engine
├── pattern_recognition.py       # ✨ LLM pattern discovery
├── prompts.py                   # System prompts
└── main.py                      # Entry point
```

✨ = New advanced features

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

## ✅ Advanced Features (Implemented)

The Python version now includes all advanced continuity and learning features:

### Memory & Learning System
- **Dual-layer Memory**: Short-term (recent trades) and long-term (lessons, patterns, personality)
- **Personality Traits**: AI develops trading personality based on history (risk tolerance, patience, confidence)
- **Post-Trade Analysis**: Automatic analysis of every completed trade to extract learnings
- **Lesson Storage**: Insights stored and recalled in future decisions

### Dynamic AI Evolution
- **Evolving Prompts**: AI prompts adapt based on performance (normal/crisis/fresh modes)
- **Crisis Mode**: Activates during drawdowns with defensive parameters
- **Fresh Perspective Mode**: Resets biases during prolonged underperformance
- **Self-Reflection**: AI required to reflect on emotional state in every decision

### LLM-Powered Backtesting
- **AI-Driven Backtesting**: Uses actual AI to make decisions on historical data
- **Insight Generation**: LLM analyzes backtest results and suggests improvements
- **Strategy Validation**: Test strategies before live deployment

### Pattern Recognition
- **LLM Pattern Discovery**: AI identifies winning/losing patterns from trade history
- **Mistake Analysis**: Categorizes common errors (entry, exit, risk, psychological)
- **Market Regime Detection**: AI classifies current market conditions
- **Strategy Improvement**: Generates actionable suggestions to improve performance

## 📖 Using Advanced Features

### Running with Enhanced Orchestrator

```python
from src.config import get_config
from src.database import init_database
from src.exchange_client import OKXClient
from src.ai_provider_enhanced import EnhancedAnthropicProvider
from src.risk_manager import RiskManager
from src.orchestrator_enhanced import EnhancedTradingOrchestrator
from src.prompts import get_system_prompt

# Initialize components
config = get_config()
database = init_database(config.database.path)
exchange = OKXClient(config.exchange)
ai_provider = EnhancedAnthropicProvider(config.ai, database)
risk_manager = RiskManager(config.risk, database)

# Create enhanced orchestrator
orchestrator = EnhancedTradingOrchestrator(
    config=config,
    exchange=exchange,
    ai_provider=ai_provider,
    risk_manager=risk_manager,
    database=database,
    system_prompt=get_system_prompt()
)

# Start trading with full memory and learning
await orchestrator.start()
```

### Running Backtests

```python
from src.backtesting import LLMBacktester
from datetime import datetime, timedelta

# Initialize backtester
backtester = LLMBacktester(
    config=config,
    ai_provider=ai_provider,
    risk_manager=risk_manager,
    database=database
)

# Load historical data (implement your data source)
historical_data = {
    'BTC-USDT-SWAP': btc_dataframe,
    'ETH-USDT-SWAP': eth_dataframe
}

# Run backtest
result = await backtester.run_backtest(
    historical_data=historical_data,
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    initial_capital=10000.0
)

# View results
print(f"Total P&L: ${result.performance.total_pnl:+.2f}")
print(f"Win Rate: {result.performance.win_rate:.1f}%")
print(f"Sharpe Ratio: {result.performance.sharpe_ratio:.2f}")
print("\nAI Insights:")
print(result.ai_insights)
```

### Discovering Patterns

```python
from src.pattern_recognition import discover_trading_edges

# Run comprehensive pattern discovery
insights = await discover_trading_edges(
    database=database,
    ai_config=config.ai
)

# View discovered patterns
print(f"Patterns found: {len(insights['patterns'])}")
for pattern in insights['patterns']:
    print(f"- {pattern.pattern_type}: {pattern.description}")

# View common mistakes
if insights['common_mistakes']:
    print("\nCommon Mistakes:")
    for category, mistakes in insights['common_mistakes'].items():
        print(f"\n{category}:")
        for mistake in mistakes:
            print(f"  - {mistake}")

# View improvement suggestions
print("\nSuggested Improvements:")
for suggestion in insights['improvement_suggestions']:
    print(f"  - {suggestion}")
```

### Analyzing Post-Trade

```python
from src.post_trade_analysis import PostTradeAnalyzer

analyzer = PostTradeAnalyzer(database)

# Analyze a completed trade
trade = database.get_trades(limit=1)[0]
analysis = analyzer.analyze_trade(trade)

print(f"Outcome: {analysis.outcome}")
print(f"\nKey Takeaways:")
for takeaway in analysis.key_takeaways:
    print(f"  - {takeaway}")

print(f"\nWhat Worked:")
for item in analysis.what_worked:
    print(f"  ✓ {item}")

print(f"\nWhat Didn't Work:")
for item in analysis.what_didnt_work:
    print(f"  ✗ {item}")

print(f"\nRecommendations:")
for rec in analysis.recommendations:
    print(f"  → {rec}")
```

## 🔮 Future Enhancements

- [ ] Multi-agent competition (multiple AI strategies competing)
- [ ] Web dashboard (FastAPI + React)
- [ ] Additional exchanges (Binance, Coinbase)
- [ ] Real-time monitoring with Prometheus/Grafana
- [ ] Advanced ML models for price prediction
- [ ] Social sentiment analysis

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
