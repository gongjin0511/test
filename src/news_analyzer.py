"""
市场新闻和情绪分析系统
使用LLM分析加密货币新闻、社交媒体情绪和市场事件
"""

import asyncio
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import anthropic
import aiohttp
from .types import MarketSentiment, NewsItem
from .config import AIConfig
import logging
import json


class NewsAnalyzer:
    """
    LLM驱动的新闻和市场情绪分析器

    功能：
    1. 抓取加密货币相关新闻
    2. 使用LLM分析新闻情绪和影响
    3. 识别市场移动事件
    4. 生成可操作的交易洞察
    """

    def __init__(
        self,
        ai_config: AIConfig,
        logger: Optional[logging.Logger] = None
    ):
        self.config = ai_config
        self.logger = logger or logging.getLogger(__name__)
        self.client = anthropic.Anthropic(api_key=ai_config.api_key)
        self.news_cache: List[NewsItem] = []
        self.last_fetch = 0

    async def fetch_crypto_news(
        self,
        symbols: List[str] = ["BTC", "ETH"],
        max_articles: int = 20
    ) -> List[NewsItem]:
        """
        抓取加密货币新闻

        来源：
        - CoinDesk
        - CoinTelegraph
        - Crypto Twitter (如果有API)
        - Reddit r/cryptocurrency
        """

        self.logger.info(f"📰 Fetching crypto news for {symbols}...")

        news_items = []

        try:
            # 示例：从多个来源抓取新闻
            # 实际生产环境需要实现具体的新闻API集成

            # 1. CoinDesk API (示例)
            # coindesk_news = await self._fetch_coindesk(symbols)
            # news_items.extend(coindesk_news)

            # 2. CryptoCompare News API
            # cryptocompare_news = await self._fetch_cryptocompare(symbols)
            # news_items.extend(cryptocompare_news)

            # 3. Twitter/X API (需要API密钥)
            # twitter_sentiment = await self._fetch_twitter(symbols)
            # news_items.extend(twitter_sentiment)

            # 临时：模拟新闻数据用于演示
            # 在生产环境中，替换为真实API调用
            self.logger.warning("⚠️ Using simulated news data - implement real news APIs")
            news_items = await self._fetch_simulated_news(symbols)

            self.news_cache = news_items
            self.last_fetch = int(time.time())

            self.logger.info(f"✅ Fetched {len(news_items)} news items")
            return news_items

        except Exception as e:
            self.logger.error(f"Error fetching news: {e}")
            return []

    async def analyze_market_sentiment(
        self,
        news_items: List[NewsItem],
        symbol: str
    ) -> MarketSentiment:
        """
        使用LLM分析新闻并生成市场情绪

        返回：
        - 总体情绪评分 (-1 到 +1)
        - 情绪类别（极度看空/看空/中性/看涨/极度看涨）
        - 关键主题和事件
        - 交易建议
        """

        if not news_items:
            self.logger.warning("No news items to analyze")
            return self._create_neutral_sentiment(symbol)

        self.logger.info(f"🧠 Analyzing sentiment for {symbol} from {len(news_items)} news items...")

        # 准备新闻摘要给LLM
        news_summary = self._prepare_news_summary(news_items, symbol)

        # 构建分析提示词
        prompt = f"""分析以下关于 {symbol} 的加密货币新闻和市场信息，生成市场情绪评估。

{news_summary}

请提供JSON格式的分析：

{{
    "sentiment_score": <-1.0 到 +1.0 的数值>,
    "sentiment_label": "extremely_bearish|bearish|neutral|bullish|extremely_bullish",
    "confidence": <0.0 到 1.0>,
    "key_themes": ["主题1", "主题2", "主题3"],
    "major_events": ["重大事件1", "重大事件2"],
    "price_impact": "short_term|medium_term|long_term",
    "impact_magnitude": "negligible|minor|moderate|significant|major",
    "trading_recommendation": "详细的交易建议",
    "risk_factors": ["风险因素1", "风险因素2"],
    "opportunities": ["机会1", "机会2"],
    "summary": "简短的情绪总结"
}}

考虑因素：
1. 新闻的可信度和来源质量
2. 事件的时效性（最新的更重要）
3. 潜在的价格影响
4. 市场情绪变化趋势
5. 与其他加密货币的相关性

要客观、理性，避免过度反应。"""

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=1500,
                temperature=0.5,
                system="""你是一位专业的加密货币市场分析师，擅长从新闻和社交媒体中提取市场情绪。
你的分析客观、准确，既不过度看涨也不过度看空。
你能识别噪音和真正重要的市场移动事件。""",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text

            # 解析JSON响应
            sentiment_data = self._extract_json_from_response(response_text)

            sentiment = MarketSentiment(
                symbol=symbol,
                timestamp=int(time.time() * 1000),
                sentiment_score=sentiment_data["sentiment_score"],
                sentiment_label=sentiment_data["sentiment_label"],
                confidence=sentiment_data["confidence"],
                key_themes=sentiment_data["key_themes"],
                major_events=sentiment_data["major_events"],
                price_impact=sentiment_data["price_impact"],
                impact_magnitude=sentiment_data["impact_magnitude"],
                trading_recommendation=sentiment_data["trading_recommendation"],
                risk_factors=sentiment_data["risk_factors"],
                opportunities=sentiment_data["opportunities"],
                summary=sentiment_data["summary"],
                news_count=len(news_items)
            )

            self.logger.info(f"✅ Sentiment analysis complete:")
            self.logger.info(f"   Score: {sentiment.sentiment_score:.2f} ({sentiment.sentiment_label})")
            self.logger.info(f"   Confidence: {sentiment.confidence * 100:.0f}%")
            self.logger.info(f"   Impact: {sentiment.impact_magnitude} {sentiment.price_impact}")
            self.logger.info(f"   Summary: {sentiment.summary[:100]}...")

            return sentiment

        except Exception as e:
            self.logger.error(f"Error in sentiment analysis: {e}")
            return self._create_neutral_sentiment(symbol)

    async def detect_breaking_news(
        self,
        news_items: List[NewsItem]
    ) -> List[Dict]:
        """
        使用LLM检测突发新闻和市场移动事件

        返回需要立即关注的新闻列表
        """

        if not news_items:
            return []

        # 只分析最近1小时的新闻
        recent_cutoff = int(time.time() * 1000) - (60 * 60 * 1000)
        recent_news = [n for n in news_items if n.timestamp > recent_cutoff]

        if not recent_news:
            return []

        self.logger.info(f"🚨 Checking for breaking news in {len(recent_news)} recent items...")

        news_list = "\n".join([
            f"- [{n.source}] {n.title}\n  {n.summary[:200]}..."
            for n in recent_news[:10]
        ])

        prompt = f"""分析以下最近的加密货币新闻，识别可能导致价格剧烈波动的突发事件。

最近新闻：
{news_list}

识别以下类型的突发新闻：
1. 监管消息（SEC批准、禁令等）
2. 重大技术问题（漏洞、攻击、网络故障）
3. 重大合作/采用（机构进场、大型企业采用）
4. 宏观经济事件（利率决定、通胀数据）
5. 行业重大事件（交易所问题、大型项目失败）

返回JSON数组：
[
    {{
        "title": "新闻标题",
        "urgency": "critical|high|medium",
        "expected_impact": "描述预期的价格影响",
        "recommended_action": "建议的交易行动",
        "affected_symbols": ["BTC", "ETH"]
    }}
]

如果没有重要突发新闻，返回空数组 []。"""

        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=1000,
                temperature=0.3,
                system="你是突发新闻检测专家，只标记真正重要的市场移动事件。",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text
            breaking_news = self._extract_json_from_response(response_text)

            if breaking_news:
                self.logger.warning(f"🚨 {len(breaking_news)} breaking news items detected!")
                for news in breaking_news:
                    self.logger.warning(f"   [{news['urgency'].upper()}] {news['title']}")

            return breaking_news if isinstance(breaking_news, list) else []

        except Exception as e:
            self.logger.error(f"Error detecting breaking news: {e}")
            return []

    async def generate_news_context_for_trading(
        self,
        symbol: str,
        sentiment: MarketSentiment,
        breaking_news: List[Dict]
    ) -> str:
        """
        生成格式化的新闻上下文，用于交易决策
        """

        context = "# 📰 市场新闻和情绪分析\n\n"

        # 总体情绪
        context += f"## {symbol} 市场情绪\n\n"

        sentiment_emoji = {
            "extremely_bearish": "📉🔴",
            "bearish": "📉",
            "neutral": "➡️",
            "bullish": "📈",
            "extremely_bullish": "📈🟢"
        }

        emoji = sentiment_emoji.get(sentiment.sentiment_label, "❓")

        context += f"**情绪评分**: {sentiment.sentiment_score:+.2f} {emoji} ({sentiment.sentiment_label})\n"
        context += f"**置信度**: {sentiment.confidence * 100:.0f}%\n"
        context += f"**预期影响**: {sentiment.impact_magnitude} {sentiment.price_impact}\n\n"

        context += f"**市场总结**: {sentiment.summary}\n\n"

        # 关键主题
        if sentiment.key_themes:
            context += "**关键主题**:\n"
            for theme in sentiment.key_themes:
                context += f"- {theme}\n"
            context += "\n"

        # 重大事件
        if sentiment.major_events:
            context += "**重大事件**:\n"
            for event in sentiment.major_events:
                context += f"- {event}\n"
            context += "\n"

        # 突发新闻
        if breaking_news:
            context += "## 🚨 突发新闻警报\n\n"
            for news in breaking_news:
                urgency_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡"}
                emoji = urgency_emoji.get(news["urgency"], "⚪")
                context += f"### {emoji} {news['title']}\n"
                context += f"**紧急程度**: {news['urgency']}\n"
                context += f"**预期影响**: {news['expected_impact']}\n"
                context += f"**建议行动**: {news['recommended_action']}\n"
                context += f"**影响币种**: {', '.join(news['affected_symbols'])}\n\n"

        # 风险和机会
        context += "## 风险与机会\n\n"

        if sentiment.risk_factors:
            context += "**风险因素**:\n"
            for risk in sentiment.risk_factors:
                context += f"- ⚠️ {risk}\n"
            context += "\n"

        if sentiment.opportunities:
            context += "**交易机会**:\n"
            for opp in sentiment.opportunities:
                context += f"- ✅ {opp}\n"
            context += "\n"

        # 交易建议
        context += f"## 基于新闻的交易建议\n\n{sentiment.trading_recommendation}\n\n"

        context += "---\n\n"
        context += f"*基于 {sentiment.news_count} 条新闻分析 | 更新时间: {datetime.now():%H:%M:%S}*\n"

        return context

    def _prepare_news_summary(self, news_items: List[NewsItem], symbol: str) -> str:
        """准备新闻摘要给LLM分析"""

        summary = f"新闻总数: {len(news_items)}\n"
        summary += f"时间范围: 最近 {self._get_time_range(news_items)} 小时\n\n"

        # 按相关性和时效性排序
        relevant_news = [n for n in news_items if symbol in n.content or symbol in n.title]
        other_news = [n for n in news_items if n not in relevant_news]

        if relevant_news:
            summary += f"## 直接相关新闻 ({len(relevant_news)}条)\n\n"
            for i, news in enumerate(relevant_news[:10], 1):
                age = self._get_news_age(news.timestamp)
                summary += f"{i}. **[{news.source}]** {news.title}\n"
                summary += f"   时间: {age} | 情绪: {news.sentiment or '未知'}\n"
                summary += f"   {news.summary[:300]}\n\n"

        if other_news:
            summary += f"## 市场整体新闻 ({len(other_news)}条)\n\n"
            for i, news in enumerate(other_news[:5], 1):
                age = self._get_news_age(news.timestamp)
                summary += f"{i}. **[{news.source}]** {news.title}\n"
                summary += f"   时间: {age}\n"
                summary += f"   {news.summary[:200]}\n\n"

        return summary

    def _get_time_range(self, news_items: List[NewsItem]) -> str:
        """计算新闻时间范围"""
        if not news_items:
            return "0"

        now = int(time.time() * 1000)
        oldest = min(n.timestamp for n in news_items)
        hours = (now - oldest) / (1000 * 60 * 60)
        return f"{hours:.1f}"

    def _get_news_age(self, timestamp: int) -> str:
        """计算新闻发布时间"""
        now = int(time.time() * 1000)
        diff_minutes = (now - timestamp) / (1000 * 60)

        if diff_minutes < 60:
            return f"{int(diff_minutes)}分钟前"
        elif diff_minutes < 24 * 60:
            return f"{int(diff_minutes / 60)}小时前"
        else:
            return f"{int(diff_minutes / (24 * 60))}天前"

    def _extract_json_from_response(self, response_text: str) -> dict:
        """从LLM响应中提取JSON"""

        # 尝试找到JSON代码块
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            json_text = response_text[start:end].strip()
        else:
            json_text = response_text.strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            self.logger.error(f"Response: {response_text}")
            raise

    def _create_neutral_sentiment(self, symbol: str) -> MarketSentiment:
        """创建中性情绪（当分析失败时）"""
        return MarketSentiment(
            symbol=symbol,
            timestamp=int(time.time() * 1000),
            sentiment_score=0.0,
            sentiment_label="neutral",
            confidence=0.3,
            key_themes=["无足够新闻数据"],
            major_events=[],
            price_impact="negligible",
            impact_magnitude="negligible",
            trading_recommendation="由于缺乏新闻数据，建议依赖技术分析进行决策。",
            risk_factors=["新闻数据不足"],
            opportunities=[],
            summary="当前没有足够的新闻数据进行情绪分析。",
            news_count=0
        )

    async def _fetch_simulated_news(self, symbols: List[str]) -> List[NewsItem]:
        """
        模拟新闻数据用于演示
        生产环境应该替换为真实API调用
        """

        now = int(time.time() * 1000)

        # 模拟一些新闻
        simulated_news = [
            NewsItem(
                title=f"{symbols[0]} 价格突破关键阻力位，分析师预测继续上涨",
                summary="技术分析显示强劲的上升趋势，多个指标显示买入信号。交易量显著增加，表明市场参与者信心增强。",
                source="CoinDesk",
                url="https://coindesk.com/example1",
                timestamp=now - 30 * 60 * 1000,  # 30分钟前
                content="详细的新闻内容...",
                sentiment="bullish"
            ),
            NewsItem(
                title="美联储利率决定即将公布，加密市场保持谨慎",
                summary="投资者在等待美联储利率决定，市场整体交易量下降。分析师建议保持防御性仓位。",
                source="Bloomberg Crypto",
                url="https://bloomberg.com/example2",
                timestamp=now - 2 * 60 * 60 * 1000,  # 2小时前
                content="详细的新闻内容...",
                sentiment="neutral"
            ),
            NewsItem(
                title=f"链上数据显示{symbols[1]}鲸鱼地址增持",
                summary="区块链分析显示大型持有者正在积累，这通常被视为看涨信号。链上活动增加。",
                source="Glassnode",
                url="https://glassnode.com/example3",
                timestamp=now - 4 * 60 * 60 * 1000,  # 4小时前
                content="详细的新闻内容...",
                sentiment="bullish"
            ),
            NewsItem(
                title="加密交易所报告异常高的提款量",
                summary="某主要交易所的提款量激增，引发市场对流动性的担忧。建议用户保持警惕。",
                source="CryptoQuant",
                url="https://cryptoquant.com/example4",
                timestamp=now - 6 * 60 * 60 * 1000,  # 6小时前
                content="详细的新闻内容...",
                sentiment="bearish"
            )
        ]

        return simulated_news

    # 以下是真实API集成示例（需要API密钥）

    async def _fetch_cryptocompare_news(self, symbols: List[str]) -> List[NewsItem]:
        """
        从CryptoCompare获取新闻（需要API密钥）
        https://min-api.cryptocompare.com/documentation
        """
        # TODO: 实现CryptoCompare API集成
        # API_KEY = "your_cryptocompare_api_key"
        # url = f"https://min-api.cryptocompare.com/data/v2/news/?lang=EN&api_key={API_KEY}"
        pass

    async def _fetch_coindesk_rss(self) -> List[NewsItem]:
        """
        从CoinDesk RSS获取新闻
        """
        # TODO: 实现RSS解析
        pass

    async def _fetch_twitter_sentiment(self, symbols: List[str]) -> List[NewsItem]:
        """
        从Twitter/X获取社交媒体情绪（需要API密钥）
        """
        # TODO: 实现Twitter API v2集成
        pass


class SentimentAggregator:
    """
    情绪聚合器 - 整合多个来源的情绪分析
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.sentiment_history: Dict[str, List[MarketSentiment]] = {}

    def add_sentiment(self, sentiment: MarketSentiment):
        """添加情绪数据到历史"""
        symbol = sentiment.symbol
        if symbol not in self.sentiment_history:
            self.sentiment_history[symbol] = []

        self.sentiment_history[symbol].append(sentiment)

        # 只保留最近24小时的数据
        cutoff = int(time.time() * 1000) - (24 * 60 * 60 * 1000)
        self.sentiment_history[symbol] = [
            s for s in self.sentiment_history[symbol]
            if s.timestamp > cutoff
        ]

    def get_sentiment_trend(self, symbol: str, hours: int = 6) -> str:
        """
        获取情绪趋势：improving, declining, stable
        """
        if symbol not in self.sentiment_history:
            return "unknown"

        cutoff = int(time.time() * 1000) - (hours * 60 * 60 * 1000)
        recent = [s for s in self.sentiment_history[symbol] if s.timestamp > cutoff]

        if len(recent) < 2:
            return "insufficient_data"

        # 计算趋势
        scores = [s.sentiment_score for s in sorted(recent, key=lambda x: x.timestamp)]
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        diff = avg_second - avg_first

        if diff > 0.2:
            return "improving"
        elif diff < -0.2:
            return "declining"
        else:
            return "stable"

    def get_average_sentiment(self, symbol: str, hours: int = 6) -> float:
        """获取平均情绪分数"""
        if symbol not in self.sentiment_history:
            return 0.0

        cutoff = int(time.time() * 1000) - (hours * 60 * 60 * 1000)
        recent = [s for s in self.sentiment_history[symbol] if s.timestamp > cutoff]

        if not recent:
            return 0.0

        return sum(s.sentiment_score for s in recent) / len(recent)
