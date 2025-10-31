"""
Trading Orchestrator - Main control loop
"""

import asyncio
import time
from typing import Dict
from .types import MarketState, TradingDecision, DecisionRecord
from .config import SystemConfig
from .database import TradingDatabase
from .exchange_client import OKXClient
from .ai_provider import AnthropicProvider
from .risk_manager import RiskManager


class TradingOrchestrator:
    """Main trading orchestrator"""

    def __init__(
        self,
        config: SystemConfig,
        exchange: OKXClient,
        ai_provider: AnthropicProvider,
        risk_manager: RiskManager,
        database: TradingDatabase,
        system_prompt: str
    ):
        self.config = config
        self.exchange = exchange
        self.ai_provider = ai_provider
        self.risk_manager = risk_manager
        self.database = database
        self.system_prompt = system_prompt
        self.is_running = False
        self.task = None

    async def start(self):
        """Start the trading system"""
        if self.is_running:
            print("⚠️  Trading system is already running")
            return

        print("🚀 Starting trading system...")

        try:
            # Test connection
            connected = await self.exchange.test_connection()
            if not connected:
                raise Exception("Failed to connect to exchange")

            print("✅ Connected to OKX exchange")

            self.is_running = True

            # Log start event
            self.database.save_decision(DecisionRecord(
                timestamp=int(time.time() * 1000),
                market_state='{"event": "system_started"}',
                ai_output='{"event": "system_started"}',
                risk_approved=True
            ))

            print("✅ Trading system started successfully")
            print(f"✅ Decision cycles every {self.config.trading.decision_interval_ms / 1000} seconds")

            # Start decision loop
            self.task = asyncio.create_task(self._decision_loop())

        except Exception as e:
            print(f"❌ Failed to start trading system: {e}")
            self.is_running = False
            raise

    async def stop(self):
        """Stop the trading system"""
        if not self.is_running:
            return

        print("🛑 Stopping trading system...")

        self.is_running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        # Log stop event
        self.database.save_decision(DecisionRecord(
            timestamp=int(time.time() * 1000),
            market_state='{"event": "system_stopped"}',
            ai_output='{"event": "system_stopped"}',
            risk_approved=True
        ))

        print("✅ Trading system stopped")

    async def _decision_loop(self):
        """Main decision loop"""
        while self.is_running:
            try:
                await self._run_decision_cycle()

                # Wait for next cycle
                await asyncio.sleep(self.config.trading.decision_interval_ms / 1000)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Error in decision cycle: {e}")
                # Log error but continue
                self.database.save_decision(DecisionRecord(
                    timestamp=int(time.time() * 1000),
                    market_state='{"error": "cycle_error"}',
                    ai_output=f'{{"error": "{str(e)}"}}',
                    risk_approved=False,
                    rejection_reason="Cycle error occurred"
                ))

                # Wait a bit before retrying
                await asyncio.sleep(10)

    async def _run_decision_cycle(self):
        """Run a single decision cycle"""
        cycle_start = time.time()

        print("━" * 60)
        print("🔄 Starting decision cycle")
        print("━" * 60)

        # 1. Collect market data
        print("📊 Collecting market data...")
        market_state = await self._collect_market_data()

        # 2. Generate AI decision
        print("🧠 Generating AI decision...")
        ai_start = time.time()
        decision = await self.ai_provider.generate_decision(market_state, self.system_prompt)
        ai_time = int((time.time() - ai_start) * 1000)

        print(f"✅ AI decision generated:")
        print(f"   - Action: {decision.action.value}")
        print(f"   - Symbol: {decision.symbol}")
        print(f"   - Confidence: {decision.confidence:.2f}")
        print(f"   - Execution time: {ai_time}ms")

        # 3. Validate with risk management
        print("🛡️  Validating decision...")
        validation = self.risk_manager.validate_decision(decision, market_state)

        # 4. Save decision
        import json
        self.database.save_decision(DecisionRecord(
            timestamp=int(time.time() * 1000),
            market_state=json.dumps(market_state.model_dump(), default=str),
            ai_output=json.dumps(decision.model_dump(), default=str),
            risk_approved=validation.approved,
            rejection_reason=validation.reason,
            execution_time=ai_time
        ))

        # 5. Execute if approved
        if validation.approved:
            print("✅ Decision approved")
            # In production: execute trade here
            print(f"   (Trade execution not implemented in demo)")
        else:
            print(f"❌ Decision rejected: {validation.reason}")

        cycle_time = int((time.time() - cycle_start) * 1000)
        print("━" * 60)
        print(f"✅ Decision cycle completed in {cycle_time}ms")
        print("━" * 60)

    async def _collect_market_data(self) -> MarketState:
        """Collect market data from exchange"""
        # Get account state
        account = await self.exchange.get_account_state()

        # Get market data for all pairs
        pairs: Dict = {}
        for symbol in self.config.trading.trading_pairs:
            try:
                market_data = await self.exchange.get_market_data(symbol)
                pairs[symbol] = market_data
            except Exception as e:
                print(f"⚠️  Failed to get market data for {symbol}: {e}")

        # Get latest performance metrics
        performance = self.database.get_latest_performance()

        return MarketState(
            timestamp=int(time.time() * 1000),
            pairs=pairs,
            account=account,
            performance_metrics=performance
        )
