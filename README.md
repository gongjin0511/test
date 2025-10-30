# OKX AI Trading System

An autonomous AI-powered cryptocurrency trading system for OKX exchange, inspired by [nof1.ai's Alpha Arena](https://nof1.ai/). This system uses Large Language Models (LLMs) to make trading decisions on cryptocurrency perpetual futures with zero human intervention.

## 🎯 Overview

This system implements the core architecture of nof1.ai's approach:
- **AI Decision Engine**: Uses Claude (Anthropic) or GPT (OpenAI) to analyze market data and generate trading decisions
- **Autonomous Trading**: Fully automated trading with configurable decision intervals (default: 3 minutes)
- **Risk Management**: Built-in safeguards including position limits, leverage caps, stop-loss enforcement, and circuit breakers
- **Performance Tracking**: Comprehensive metrics including Sharpe ratio, win rate, max drawdown, and PnL tracking
- **Transparency**: All decisions, trades, and performance metrics are logged to SQLite database

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Trading Orchestrator                        │
│              (Main Control Loop - Every 3 min)               │
└────────────┬──────────────────────────────┬─────────────────┘
             │                              │
    ┌────────▼────────┐          ┌─────────▼─────────┐
    │  Market Data    │          │  AI Decision      │
    │   Collector     │─────────▶│     Engine        │
    │  (OKX API)      │          │  (Claude/GPT)     │
    └─────────────────┘          └─────────┬─────────┘
                                           │
                                  ┌────────▼─────────┐
                                  │ Risk Management  │
                                  │    Validator     │
                                  └────────┬─────────┘
                                           │
                                  ┌────────▼─────────┐
                                  │  Trade Executor  │
                                  │   (OKX Orders)   │
                                  └──────────────────┘
```

## ✨ Key Features

### AI-Powered Decision Making
- Analyzes market data every N minutes (configurable)
- Receives price data, technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR)
- Considers current positions and performance metrics
- Generates structured trading decisions with confidence scores and exit plans

### Comprehensive Risk Management
- ✅ Position size limits (default: max 20% per trade)
- ✅ Leverage limits (default: max 5x)
- ✅ Mandatory stop-loss enforcement
- ✅ Daily loss circuit breaker (halts trading on excessive losses)
- ✅ Portfolio exposure limits
- ✅ Minimum confidence threshold filtering

### Trading Capabilities
- **Long positions**: Buy when expecting price increases
- **Short positions**: Sell when expecting price decreases
- **Automatic exit management**: Stop-loss and take-profit orders
- **Position monitoring**: Real-time tracking of exit conditions

### Performance Analytics
- **Sharpe Ratio**: Risk-adjusted returns
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Total wins / Total losses
- **Max Drawdown**: Largest peak-to-trough decline
- **Daily/Total PnL**: Absolute and percentage returns

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- OKX account with API keys ([Get API keys](https://www.okx.com/account/my-api))
- Anthropic API key ([Get Claude API](https://www.anthropic.com/api)) or OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd test
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure environment**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
# OKX API Configuration
OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here
OKX_PASSPHRASE=your_passphrase_here
OKX_API_ENV=demo  # Use 'demo' for testnet, 'production' for live trading

# AI Configuration
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here
AI_MODEL=claude-sonnet-4.5

# Trading Configuration
INITIAL_CAPITAL=10000
TRADING_MODE=testnet
DECISION_INTERVAL_MS=180000  # 3 minutes
```

4. **Build the project**
```bash
npm run build
```

5. **Run the trading system**
```bash
npm start
```

Or for development with auto-reload:
```bash
npm run dev
```

## 📖 Configuration Guide

### Trading Pairs
Specify which cryptocurrencies to trade (comma-separated):
```bash
TRADING_PAIRS=BTC-USDT-SWAP,ETH-USDT-SWAP,SOL-USDT-SWAP
```

### Risk Parameters
```bash
MAX_LEVERAGE=5                      # Maximum leverage per position
MAX_POSITION_SIZE_PERCENTAGE=20    # Max % of capital per trade
STOP_LOSS_PERCENTAGE=5             # Maximum stop-loss per trade
MAX_DAILY_LOSS_PERCENT=10          # Circuit breaker threshold
MIN_CONFIDENCE_THRESHOLD=0.6       # Min AI confidence to execute
```

### AI Configuration
```bash
AI_PROVIDER=anthropic              # anthropic, openai, or custom
AI_MODEL=claude-sonnet-4.5         # or gpt-4o, etc.
AI_TEMPERATURE=0.7                 # 0.0 (conservative) to 1.0 (creative)
```

### Decision Interval
```bash
DECISION_INTERVAL_MS=180000        # 180000ms = 3 minutes (nof1.ai uses 2-3 min)
```

## 🧠 How It Works

### Decision Cycle (Every 3 Minutes)

1. **Collect Market Data**
   - Fetch current prices, 24h changes, volume
   - Calculate technical indicators (SMA, RSI, MACD, etc.)
   - Get account state (balance, positions, PnL)

2. **Generate AI Decision**
   - Send market data + system prompt to LLM
   - AI analyzes data and generates structured decision
   - Includes: action, symbol, quantity, leverage, confidence, reasoning, exit plan

3. **Risk Validation**
   - Check position size limits
   - Verify leverage constraints
   - Ensure stop-loss is set
   - Validate against circuit breaker
   - Approve or reject decision

4. **Execute Trade** (if approved)
   - Place market order on OKX
   - Set stop-loss and take-profit orders
   - Log trade to database

5. **Monitor Positions**
   - Check existing positions against exit conditions
   - Automatically close positions when stop-loss or take-profit hit

6. **Update Metrics**
   - Calculate performance metrics
   - Update risk exposure
   - Save to database

### AI Decision Format

The AI generates decisions in this JSON format:

```json
{
  "action": "OPEN_LONG",
  "symbol": "BTC-USDT-SWAP",
  "quantity": 0.5,
  "leverage": 3,
  "confidence": 0.75,
  "reasoning": "BTC showing bullish momentum with RSI at 45 and price above SMA(20). MACD positive divergence.",
  "exitPlan": {
    "takeProfit": 8.0,
    "stopLoss": 4.0,
    "invalidation": "Exit if price falls below SMA(50) or RSI drops below 30"
  }
}
```

## 📊 Performance Monitoring

### Database Structure

All data is stored in SQLite (`./data/trading.db`):

- **trades**: All executed trades with entry/exit prices, PnL, reasoning
- **decisions**: All AI decisions (including rejected ones)
- **performance**: Historical performance metrics snapshots

### Viewing Data

Use any SQLite client to query the database:

```bash
sqlite3 ./data/trading.db

-- View recent trades
SELECT * FROM trades ORDER BY timestamp DESC LIMIT 10;

-- View performance metrics
SELECT * FROM performance ORDER BY timestamp DESC LIMIT 1;

-- View AI decisions
SELECT ai_output, risk_approved, rejection_reason
FROM decisions
ORDER BY timestamp DESC
LIMIT 10;
```

### Logs

Logs are written to `./logs/trading.log`:
- **INFO**: Trade executions, decisions, system events
- **WARN**: Risk violations, rejected decisions
- **ERROR**: Execution failures, API errors
- **DEBUG**: Detailed market data, AI prompts (if LOG_LEVEL=debug)

## 🛡️ Risk Management Details

### Position Limits
- **Max position size**: 20% of total equity per trade
- **Max concurrent positions**: 3 (configurable)
- **Max portfolio exposure**: 80% of total equity

### Leverage Management
- Default max: 5x
- OKX supports up to 125x, but higher leverage = higher risk
- AI can choose lower leverage for less risky trades

### Circuit Breaker
Automatically halts trading when:
- Daily loss exceeds threshold (default: 10%)
- Prevents catastrophic losses during unfavorable market conditions
- Requires manual reset (restart system after investigating)

### Stop-Loss Enforcement
- Every position MUST have a stop-loss (configurable)
- Maximum stop-loss: 5% (configurable)
- Automatically closes position when price hits stop-loss

## 🔧 Advanced Usage

### Running Multiple AI Models

You can run multiple instances with different AI models to compete:

```bash
# Terminal 1: Claude Sonnet 4.5
AI_MODEL=claude-sonnet-4.5 DB_PATH=./data/claude.db npm start

# Terminal 2: GPT-4o
AI_PROVIDER=openai AI_MODEL=gpt-4o DB_PATH=./data/gpt4.db npm start
```

### Custom System Prompt

Modify `src/ai/system-prompt.ts` to customize trading strategy:
- Change risk tolerance
- Adjust technical analysis approach
- Modify position sizing logic
- Add new indicators or conditions

### Production Deployment

For production use:

1. **Use production OKX API**
```bash
OKX_API_ENV=production
TRADING_MODE=live
```

2. **Enable real OKX API integration**
   - Replace mock implementation in `src/exchange/okx-client.ts`
   - Use official OKX Node.js SDK: `npm install okx-api`

3. **Process management**
```bash
npm install -g pm2
pm2 start npm --name "okx-trading" -- start
pm2 logs okx-trading
```

## 📚 Project Structure

```
okx-ai-trading-system/
├── src/
│   ├── ai/
│   │   ├── providers/
│   │   │   └── anthropic.ts       # Claude AI provider
│   │   └── system-prompt.ts       # AI trading instructions
│   ├── config/
│   │   └── index.ts               # Configuration loader
│   ├── database/
│   │   └── index.ts               # SQLite database layer
│   ├── exchange/
│   │   └── okx-client.ts          # OKX exchange client
│   ├── orchestrator/
│   │   └── index.ts               # Main trading loop
│   ├── risk/
│   │   └── risk-manager.ts        # Risk validation system
│   ├── trading/
│   │   └── executor.ts            # Trade execution pipeline
│   ├── types/
│   │   └── index.ts               # TypeScript type definitions
│   ├── utils/
│   │   ├── indicators.ts          # Technical indicators
│   │   ├── logger.ts              # Winston logger
│   │   └── performance.ts         # Performance calculator
│   └── index.ts                   # Main entry point
├── data/                          # Database storage (gitignored)
├── logs/                          # Log files (gitignored)
├── .env                           # Environment variables (gitignored)
├── .env.example                   # Environment template
├── package.json                   # Dependencies
├── tsconfig.json                  # TypeScript config
├── ARCHITECTURE.md                # Detailed architecture docs
└── README.md                      # This file
```

## 🚨 Important Warnings

### ⚠️ FINANCIAL RISK
- **Cryptocurrency trading is highly risky**: You can lose your entire capital
- **Start with testnet**: Always test thoroughly before using real money
- **Use small amounts**: Only trade with capital you can afford to lose
- **Not financial advice**: This is educational software, not investment advice

### ⚠️ TECHNICAL CONSIDERATIONS
- **AI is not perfect**: LLMs can make mistakes or irrational decisions
- **API limitations**: Exchange APIs can have rate limits or downtime
- **Network issues**: Internet connectivity problems can cause missed opportunities
- **Bug risk**: This is open-source software provided as-is

### ⚠️ REGULATORY
- Ensure cryptocurrency trading is legal in your jurisdiction
- Understand tax implications of automated trading
- Comply with all relevant financial regulations

## 🤝 Comparison to nof1.ai

| Feature | nof1.ai Alpha Arena | This System |
|---------|---------------------|-------------|
| Exchange | Hyperliquid | OKX |
| AI Models | Multiple (competition) | Single (configurable) |
| Decision Interval | 2-3 minutes | Configurable (default 3 min) |
| Transparency | On-chain | Local database |
| Initial Capital | $10,000 | Configurable |
| Asset Universe | BTC, ETH, SOL, XRP, DOGE, BNB | Configurable |
| Risk Management | Built-in | Comprehensive |
| Open Source | Partial | Full |

## 📝 To-Do / Future Enhancements

- [ ] Web dashboard for real-time monitoring
- [ ] Support for additional AI providers (Google Gemini, etc.)
- [ ] Backtesting engine for historical data
- [ ] Multi-agent competition mode (leaderboard)
- [ ] Support for additional exchanges (Binance, Coinbase)
- [ ] Telegram/Discord notifications
- [ ] Advanced position management (trailing stops, partial exits)
- [ ] Machine learning for strategy optimization

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Inspired by [nof1.ai's Alpha Arena](https://nof1.ai/)
- Built with [Anthropic Claude](https://www.anthropic.com/) and [OpenAI GPT](https://openai.com/)
- Powered by [OKX Exchange](https://www.okx.com/)

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check `ARCHITECTURE.md` for detailed technical documentation
- Review logs in `./logs/trading.log` for debugging

---

**Disclaimer**: This software is for educational purposes only. Cryptocurrency trading carries significant risk. Always do your own research and never invest more than you can afford to lose. The developers are not responsible for any financial losses incurred using this system.
