#!/usr/bin/env python3
"""
OKX AI Trading System - Python Edition
Main entry point
"""

import asyncio
import sys
import signal
from pathlib import Path

from .config import get_config
from .database import init_database
from .exchange_client import create_okx_client
from .ai_provider import AnthropicProvider
from .risk_manager import RiskManager
from .orchestrator import TradingOrchestrator
from .prompts import SYSTEM_PROMPT


async def main():
    """Main function"""
    print("=" * 60)
    print("  OKX AI Trading System - Python Edition")
    print("  Inspired by nof1.ai Alpha Arena")
    print("=" * 60)
    print()

    try:
        # 1. Load configuration
        print("📋 Loading configuration...")
        config = get_config()
        print(f"   - Trading mode: {config.trading.mode}")
        print(f"   - Initial capital: ${config.trading.initial_capital}")
        print(f"   - Trading pairs: {', '.join(config.trading.trading_pairs)}")
        print(f"   - AI provider: {config.ai.provider} ({config.ai.model})")
        print(f"   - Decision interval: {config.trading.decision_interval_ms / 1000}s")
        print()

        # 2. Initialize database
        print("💾 Initializing database...")
        database = init_database(config.database.path)
        print(f"   - Database path: {config.database.path}")
        print()

        # 3. Initialize exchange client
        print("🔌 Connecting to OKX exchange...")
        exchange = create_okx_client(
            config.okx.api_key,
            config.okx.secret_key,
            config.okx.passphrase,
            config.okx.testnet
        )
        connected = await exchange.test_connection()
        if not connected:
            raise Exception("Failed to connect to OKX")
        print("   - Connection successful")
        print()

        # 4. Initialize AI provider
        print("🤖 Initializing AI provider...")
        ai_provider = AnthropicProvider(config.ai)
        print(f"   - Provider: {config.ai.provider}")
        print(f"   - Model: {config.ai.model}")
        print()

        # 5. Initialize risk manager
        print("🛡️  Initializing risk manager...")
        risk_manager = RiskManager(
            config.risk,
            config.trading,
            config.trading.initial_capital
        )
        print(f"   - Max leverage: {config.trading.max_leverage}x")
        print(f"   - Max position size: {config.trading.max_position_size_percent}%")
        print(f"   - Circuit breaker: {'enabled' if config.risk.circuit_breaker_enabled else 'disabled'}")
        print()

        # 6. Create orchestrator
        print("🎯 Creating trading orchestrator...")
        orchestrator = TradingOrchestrator(
            config=config,
            exchange=exchange,
            ai_provider=ai_provider,
            risk_manager=risk_manager,
            database=database,
            system_prompt=SYSTEM_PROMPT
        )
        print()

        # 7. Setup signal handlers for graceful shutdown
        loop = asyncio.get_event_loop()

        def signal_handler(sig):
            print(f"\n{signal.Signals(sig).name} received, shutting down gracefully...")
            asyncio.create_task(orchestrator.stop())
            loop.stop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

        # 8. Start trading system
        print("🚀 Starting trading system...")
        print()
        await orchestrator.start()

        # Keep running
        print("✅ Trading system is now running")
        print("   Press Ctrl+C to stop")
        print()
        print("=" * 60)
        print()

        # Run forever
        while orchestrator.is_running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as error:
        print()
        print(f"❌ Fatal error: {error}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'database' in locals():
            database.close()


if __name__ == "__main__":
    asyncio.run(main())
