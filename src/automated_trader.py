"""
全自动化交易系统
包含健康监控、自动恢复和新闻集成
"""

import asyncio
import signal
import sys
import time
import traceback
from typing import Optional
from datetime import datetime
import logging
from pathlib import Path

from .config import get_config, SystemConfig
from .database import init_database, TradingDatabase
from .exchange_client import OKXClient
from .ai_provider_enhanced import EnhancedAnthropicProvider
from .risk_manager import RiskManager
from .orchestrator_enhanced import EnhancedTradingOrchestrator
from .news_analyzer import NewsAnalyzer, SentimentAggregator
from .prompts import get_system_prompt


class HealthMonitor:
    """健康监控系统"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.last_decision_time = time.time()
        self.error_count = 0
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        self.total_decisions = 0
        self.start_time = time.time()

    def record_decision(self):
        """记录成功决策"""
        self.last_decision_time = time.time()
        self.total_decisions += 1
        self.consecutive_errors = 0

    def record_error(self):
        """记录错误"""
        self.error_count += 1
        self.consecutive_errors += 1

    def is_healthy(self) -> bool:
        """检查系统健康状态"""

        # 检查连续错误
        if self.consecutive_errors >= self.max_consecutive_errors:
            self.logger.error(f"❌ 系统不健康: {self.consecutive_errors} 个连续错误")
            return False

        # 检查决策超时（超过10分钟没有决策）
        time_since_last = time.time() - self.last_decision_time
        if time_since_last > 600:  # 10分钟
            self.logger.error(f"❌ 系统不健康: {time_since_last/60:.1f} 分钟没有决策")
            return False

        return True

    def get_uptime(self) -> float:
        """获取运行时间（秒）"""
        return time.time() - self.start_time

    def get_status_report(self) -> str:
        """获取状态报告"""
        uptime_hours = self.get_uptime() / 3600
        return f"""
系统健康状态报告
==================
运行时间: {uptime_hours:.2f} 小时
总决策次数: {self.total_decisions}
总错误数: {self.error_count}
连续错误: {self.consecutive_errors}/{self.max_consecutive_errors}
上次决策: {time.time() - self.last_decision_time:.1f} 秒前
状态: {'✅ 健康' if self.is_healthy() else '❌ 不健康'}
==================
"""


class AutomatedTradingSystem:
    """
    全自动化交易系统

    功能：
    1. 完全自动运行，无需人工干预
    2. 集成新闻和情绪分析
    3. 健康监控和自动恢复
    4. 优雅关闭
    5. 错误处理和日志
    """

    def __init__(self, config_path: Optional[str] = None):
        # 加载配置
        self.config = get_config(config_path)

        # 设置日志
        self.logger = self._setup_logging()

        # 初始化组件
        self.database: Optional[TradingDatabase] = None
        self.exchange: Optional[OKXClient] = None
        self.ai_provider: Optional[EnhancedAnthropicProvider] = None
        self.risk_manager: Optional[RiskManager] = None
        self.orchestrator: Optional[EnhancedTradingOrchestrator] = None
        self.news_analyzer: Optional[NewsAnalyzer] = None
        self.sentiment_aggregator = SentimentAggregator(self.logger)

        # 监控和控制
        self.health_monitor = HealthMonitor(self.logger)
        self.is_running = False
        self.shutdown_requested = False

        # 新闻更新任务
        self.news_task: Optional[asyncio.Task] = None
        self.news_update_interval = 300  # 5分钟更新一次新闻

    def _setup_logging(self) -> logging.Logger:
        """设置日志系统"""

        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 配置日志
        log_file = log_dir / f"automated_trader_{datetime.now():%Y%m%d}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        logger = logging.getLogger("AutomatedTrader")
        logger.info("=" * 80)
        logger.info("🤖 自动化交易系统启动")
        logger.info("=" * 80)

        return logger

    async def initialize(self):
        """初始化所有组件"""

        self.logger.info("初始化系统组件...")

        try:
            # 数据库
            self.logger.info("📊 初始化数据库...")
            self.database = init_database(self.config.database.path)

            # 交易所客户端
            self.logger.info("🔗 初始化交易所客户端...")
            self.exchange = OKXClient(
                api_key=self.config.exchange.api_key,
                secret_key=self.config.exchange.secret_key,
                passphrase=self.config.exchange.passphrase,
                testnet=self.config.exchange.testnet
            )

            # 测试连接
            connected = await self.exchange.test_connection()
            if not connected:
                raise Exception("无法连接到OKX交易所")
            self.logger.info("✅ 交易所连接成功")

            # AI提供者（增强版，包含记忆）
            self.logger.info("🧠 初始化增强版AI提供者...")
            self.ai_provider = EnhancedAnthropicProvider(
                config=self.config.ai,
                database=self.database,
                logger=self.logger
            )

            # 风险管理
            self.logger.info("🛡️ 初始化风险管理系统...")
            self.risk_manager = RiskManager(
                config=self.config.risk,
                database=self.database,
                logger=self.logger
            )

            # 新闻分析器
            self.logger.info("📰 初始化新闻分析系统...")
            self.news_analyzer = NewsAnalyzer(
                ai_config=self.config.ai,
                logger=self.logger
            )

            # 交易编排器（增强版，包含学习）
            self.logger.info("🎯 初始化增强版交易编排器...")
            self.orchestrator = EnhancedTradingOrchestrator(
                config=self.config,
                exchange=self.exchange,
                ai_provider=self.ai_provider,
                risk_manager=self.risk_manager,
                database=self.database,
                system_prompt=get_system_prompt(),
                logger=self.logger,
                sentiment_aggregator=self.sentiment_aggregator  # 集成新闻情绪
            )

            self.logger.info("✅ 所有组件初始化完成")

        except Exception as e:
            self.logger.error(f"❌ 初始化失败: {e}")
            raise

    async def start(self):
        """启动自动化交易系统"""

        self.logger.info("=" * 80)
        self.logger.info("🚀 启动全自动化交易系统")
        self.logger.info("=" * 80)
        self.logger.info("配置:")
        self.logger.info(f"  决策间隔: {self.config.trading.decision_interval_ms / 1000} 秒")
        self.logger.info(f"  交易对: {', '.join(self.config.trading.trading_pairs)}")
        self.logger.info(f"  新闻更新间隔: {self.news_update_interval} 秒")
        self.logger.info(f"  测试网模式: {self.config.exchange.testnet}")
        self.logger.info("=" * 80)

        # 设置信号处理（优雅关闭）
        self._setup_signal_handlers()

        try:
            # 初始化
            await self.initialize()

            # 启动交易编排器
            await self.orchestrator.start()

            # 启动新闻更新任务
            self.news_task = asyncio.create_task(self._news_update_loop())

            # 启动健康监控任务
            health_task = asyncio.create_task(self._health_check_loop())

            self.is_running = True

            self.logger.info("✅ 系统完全运行中...")
            self.logger.info("按 Ctrl+C 优雅关闭")

            # 等待关闭信号
            while self.is_running and not self.shutdown_requested:
                await asyncio.sleep(1)

            # 开始关闭流程
            await self.shutdown()

        except Exception as e:
            self.logger.error(f"❌ 系统错误: {e}")
            self.logger.error(traceback.format_exc())
            await self.shutdown()
            sys.exit(1)

    async def _news_update_loop(self):
        """新闻更新循环"""

        self.logger.info("📰 新闻更新任务启动")

        while self.is_running and not self.shutdown_requested:
            try:
                # 获取新闻
                symbols_short = [s.split('-')[0] for s in self.config.trading.trading_pairs]
                news_items = await self.news_analyzer.fetch_crypto_news(
                    symbols=symbols_short,
                    max_articles=20
                )

                if news_items:
                    self.logger.info(f"📰 获取到 {len(news_items)} 条新闻")

                    # 为每个交易对分析情绪
                    for symbol in self.config.trading.trading_pairs:
                        symbol_short = symbol.split('-')[0]

                        # 分析情绪
                        sentiment = await self.news_analyzer.analyze_market_sentiment(
                            news_items=news_items,
                            symbol=symbol_short
                        )

                        # 保存到聚合器
                        self.sentiment_aggregator.add_sentiment(sentiment)

                        self.logger.info(f"  {symbol_short}: 情绪={sentiment.sentiment_score:+.2f} ({sentiment.sentiment_label})")

                    # 检测突发新闻
                    breaking_news = await self.news_analyzer.detect_breaking_news(news_items)

                    if breaking_news:
                        self.logger.warning("=" * 80)
                        self.logger.warning("🚨 检测到突发新闻!")
                        self.logger.warning("=" * 80)
                        for news in breaking_news:
                            self.logger.warning(f"[{news['urgency'].upper()}] {news['title']}")
                            self.logger.warning(f"预期影响: {news['expected_impact']}")
                            self.logger.warning(f"建议: {news['recommended_action']}")
                        self.logger.warning("=" * 80)

                # 等待下次更新
                await asyncio.sleep(self.news_update_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"新闻更新错误: {e}")
                await asyncio.sleep(60)  # 错误后等待1分钟再试

        self.logger.info("📰 新闻更新任务停止")

    async def _health_check_loop(self):
        """健康检查循环"""

        self.logger.info("❤️ 健康监控任务启动")

        while self.is_running and not self.shutdown_requested:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次

                # 检查健康状态
                if not self.health_monitor.is_healthy():
                    self.logger.error("=" * 80)
                    self.logger.error("❌ 系统健康检查失败")
                    self.logger.error(self.health_monitor.get_status_report())
                    self.logger.error("=" * 80)

                    # 尝试恢复
                    await self._attempt_recovery()

                # 每小时记录一次状态
                uptime = self.health_monitor.get_uptime()
                if int(uptime) % 3600 < 60:  # 每小时
                    self.logger.info(self.health_monitor.get_status_report())

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康检查错误: {e}")

        self.logger.info("❤️ 健康监控任务停止")

    async def _attempt_recovery(self):
        """尝试恢复系统"""

        self.logger.warning("🔄 尝试恢复系统...")

        try:
            # 重启orchestrator
            if self.orchestrator:
                await self.orchestrator.stop()
                await asyncio.sleep(5)
                await self.orchestrator.start()

            # 重置错误计数
            self.health_monitor.consecutive_errors = 0

            self.logger.info("✅ 系统恢复成功")

        except Exception as e:
            self.logger.error(f"❌ 恢复失败: {e}")
            # 如果恢复失败，关闭系统
            self.shutdown_requested = True

    async def shutdown(self):
        """优雅关闭系统"""

        if not self.is_running:
            return

        self.logger.info("=" * 80)
        self.logger.info("🛑 开始关闭系统...")
        self.logger.info("=" * 80)

        self.is_running = False

        try:
            # 停止新闻任务
            if self.news_task:
                self.news_task.cancel()
                try:
                    await self.news_task
                except asyncio.CancelledError:
                    pass

            # 停止orchestrator
            if self.orchestrator:
                await self.orchestrator.stop()

            # 关闭数据库
            if self.database:
                self.database.close()

            # 最终状态报告
            self.logger.info(self.health_monitor.get_status_report())

            self.logger.info("=" * 80)
            self.logger.info("✅ 系统已安全关闭")
            self.logger.info("=" * 80)

        except Exception as e:
            self.logger.error(f"关闭时错误: {e}")

    def _setup_signal_handlers(self):
        """设置信号处理器（优雅关闭）"""

        def signal_handler(sig, frame):
            self.logger.info(f"\n收到信号 {sig}，开始优雅关闭...")
            self.shutdown_requested = True

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """主入口函数"""

    # 创建自动化交易系统
    system = AutomatedTradingSystem()

    # 启动系统
    await system.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"严重错误: {e}")
        traceback.print_exc()
        sys.exit(1)
