"""
J.A.R.V.I.S. NLP Module
------------------------
Natural Language Processing module for intent recognition, entity extraction, and sentiment analysis.
Supports Chinese and English. Uses rule-based heuristics + lightweight classification.
"""

import re
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


# ============================================================
# Intent Definitions
# ============================================================
INTENTS = {
    "weather": [
        "天气", "温度", "湿度", "下雨", "雪", "空气质量", "aqi", "雾霾",
        "weather", "temperature", "rain", "snow", "air quality",
        "什么天气", "天气怎么样", "今天天气", "北京天气",
    ],
    "task_create": [
        "创建任务", "新建任务", "添加任务", "设置任务",
        "create task", "new task", "add task", "set task",
        "create", "task", "todo",
    ],
    "task_list": [
        "任务列表", "我的任务", "待办", "todo", "list task",
        "有什么任务", "查看所有任务",
    ],
    "data_analysis": [
        "数据分析", "分析数据", "统计", "calculate", "statistics",
        "帮我分析", "数据报告", "generate data", "generate 50 data",
        "analyze", "data analysis", "analyze test",
    ],
    "reminder": [
        "提醒我", "提醒", "闹钟", "set reminder", "remind me",
        "别忘了", "定时提醒",
    ],
    "file_operation": [
        "创建文件", "写入文件", "读取文件", "read file", "write file",
        "list directory", "查看文件", "创建文档",
    ],
    "list_tools": [
        "列出工具", "有什么工具", "可用的工具", "list tools", "可用工具",
        "有哪些工具", "工具列表", "show tools",
    ],
    "report": [
        "生成报告", "做报告", "报告", "generate report", "report",
        "月度报告", "季度报告", "年度报告",
    ],
    "status": [
        "系统状态", "status", "system status", "健康检查",
        "你好", "hello", "hi", "打招呼", "greet",
    ],
    "joke": [
        "笑话", "搞笑", "joke", "funny", "冷笑话", "逗我开心",
    ],
    "self_intro": [
        "自我介绍", "你是谁", "who are you", "what are you", "你的名字",
    ],
    "bye": [
        "再见", "拜拜", "goodbye", "bye", "下次见",
    ],
    "crypto": [
        "加密货币", "比特币", "以太坊", "狗狗币", "币价", "crypto", "bitcoin",
        "ethereum", "dogecoin", "solana", "cardano", "区块链", "数字货币",
        "比特币价格", "以太坊价格", "coin price", "cryptocurrency",
    ],
    "exchange": [
        "汇率", "货币兑换", "换算", "exchange rate", "currency",
        "美元兑人民币", "欧元兑美元", "换汇", "汇率查询",
        "多少人民币", "换算成", "exchange", "to cny", "to usd", "to eur",
        "convert", "currency convert",
    ],
    "dictionary": [
        "查单词", "单词", "词典", "dictionary", "definition", "什么意思",
        "word", "define", "词汇", "单词意思", "词汇查询", "查",
    ],
    "holiday": [
        "节假日", "放假", "假期", "公共假期", "holiday", "放假安排",
        "法定假日", "春节", "国庆", "端午", "中秋", "holidays",
        "public holiday", "法定节假日", "放假日",
    ],
    "book": [
        "查书", "书籍", "小说", "book", "search book", "找书", "图书",
        "推荐书", "书名", "作者", "search", "books", "阅读",
    ],
}

# Entity patterns
ENTITY_PATTERNS = {
    "city": re.compile(r"(北京|上海|广州|深圳|成都|杭州|武汉|南京|重庆|西安|长沙|郑州|青岛|大连|厦门|沈阳|哈尔滨|济南|合肥|福州|昆明|贵阳|南宁|兰州|乌鲁木齐|海口|呼和浩特|拉萨|天津|香港|澳门|台北)(市)?"),
    "date": re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|明天|后天|大后天|今天|昨天|\d{1,2}月\d{1,2}日)"),
    "priority": re.compile(r"(high|medium|low|高|中|低|紧急|普通|低优先级)"),
    "number": re.compile(r"(\d+)"),
    "file_path": re.compile(r"([a-zA-Z]:[/\\]|\/)[\w\-./\\]+"),
    "coin": re.compile(r"(bitcoin|ethereum|solana|dogecoin|cardano|ripple|xrp|polkadot|avalanche|polygon|litecoin|chainlink|比特币|以太坊|狗狗币)"),
    "currency": re.compile(r"\b(USD|CNY|EUR|GBP|JPY|KRW|HKD|AUD|CAD|CHF|SGD|NZD|THB|VND|MYR|IDR|PHP|INR|RUB|BRL|MXN)\b", re.IGNORECASE),
    "word": re.compile(r"(?:查|define|definition|look up|查一下)\s*([a-zA-Z]\w+)"),
    "country": re.compile(r"\b(CN|US|JP|GB|KR|HK|DE|FR|IT|ES|CA|AU|BR|IN|RU|SG|TH|MY|VN|PH|ID)\b"),
    "category": re.compile(r"(Programming|Misc|Dark|Pun|Spooky|Christmas|Any)"),
}

# Sentiment keywords (Chinese & English)
POSITIVE_WORDS = ["好", "棒", "优秀", "perfect", "great", "good", "喜欢", "满意", "thanks", "thank", "谢谢"]
NEGATIVE_WORDS = ["差", "糟糕", "垃圾", "bad", "terrible", "awful", "讨厌", "不满意", "hate", "angry", "生气"]


class NLPProcessor:
    """
    Lightweight NLP processor with intent recognition, entity extraction,
    and sentiment analysis. Designed for speed without LLM dependency.
    """

    def __init__(self):
        self.intent_index = self._build_intent_index()
        self.jokes = [
            "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 == Dec 25。",
            "如果一个线程走进酒吧，它可能会坐在那里一直等待——永远不会被释放。",
            "为什么 Python 程序员戴眼镜？因为他们不懂 C#。",
            "有一个科学家被告知只能选择一种乐器，于是他选了 Bass（贝斯/碱）。",
            "问：你怎么知道一个计算机工程师正在微笑？因为他打开了浏览器。",
        ]
        self._sentiment_cache: Dict[str, float] = {}

    # ----------------------------------------------------------
    # Intent Index Builder
    # ----------------------------------------------------------
    def _build_intent_index(self) -> Dict[str, str]:
        index: Dict[str, str] = {}
        for intent, keywords in INTENTS.items():
            for kw in keywords:
                index[kw.lower()] = intent
        return index

    # ----------------------------------------------------------
    # Intent Recognition
    # ----------------------------------------------------------
    def recognize_intent(self, text: str) -> Tuple[str, float]:
        """
        Recognize the intent of the input text.
        Returns (intent, confidence_score).
        """
        text_lower = text.lower().strip()

        # Exact match with full text
        if text_lower in self.intent_index:
            return self.intent_index[text_lower], 1.0

        # Fuzzy match: count keyword overlap
        scores: Dict[str, int] = defaultdict(int)
        for word in text_lower.split():
            word = word.strip("，。！？,.!?\"'")
            if word in self.intent_index:
                scores[self.intent_index[word]] += 1

        # Check for substring matches
        for keyword, intent in self.intent_index.items():
            if keyword in text_lower:
                scores[intent] += 1

        if not scores:
            return "unknown", 0.0

        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        # Normalize confidence (cap at 0.95)
        confidence = min(0.95, max_score / max(len(text_lower.split()), 1) + 0.3)
        return best_intent, round(confidence, 2)

    # ----------------------------------------------------------
    # Entity Extraction
    # ----------------------------------------------------------
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract structured entities from text."""
        entities = {}

        for entity_type, pattern in ENTITY_PATTERNS.items():
            match = pattern.search(text)
            if match:
                entities[entity_type] = match.group(1)

        return entities

    # ----------------------------------------------------------
    # Sentiment Analysis
    # ----------------------------------------------------------
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text. Returns score and label.
        Score range: -1.0 (negative) to +1.0 (positive).
        """
        if text in self._sentiment_cache:
            cached = self._sentiment_cache[text]
            return {"score": cached, "label": "positive" if cached > 0.1 else ("negative" if cached < -0.1 else "neutral")}

        text_lower = text.lower()
        pos_count = sum(1 for w in POSITIVE_WORDS if w in text_lower)
        neg_count = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
        total = pos_count + neg_count

        if total == 0:
            score = 0.0
        else:
            score = round((pos_count - neg_count) / total, 2)

        self._sentiment_cache[text] = score
        label = "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral")
        return {"score": score, "label": label}

    # ----------------------------------------------------------
    # Full Pipeline
    # ----------------------------------------------------------
    async def process(self, text: str) -> Dict[str, Any]:
        """
        Full NLP pipeline: intent recognition + entity extraction + sentiment analysis.
        """
        intent, confidence = self.recognize_intent(text)
        entities = self.extract_entities(text)
        sentiment = self.analyze_sentiment(text)

        return {
            "input": text,
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "sentiment": sentiment,
            "processed_at": datetime.now().isoformat(),
        }

    # ----------------------------------------------------------
    # Intent-specific Response Generator
    # ----------------------------------------------------------
    async def generate_response(self, intent: str, entities: Dict[str, Any], sentiment: Dict[str, Any], confidence: float = 0.0) -> Dict[str, Any]:
        """Generate a response based on recognized intent and entities."""

        responses = {
            "weather": f"检测到天气查询意图，置信度 {confidence:.2f}。正在为您查询【{entities.get('city', '未知城市')}】的天气信息...",
            "task_create": "好的，我来帮您创建一个任务。请告诉我任务的标题和截止日期。",
            "task_list": "让我来查看一下您的任务列表...",
            "data_analysis": "数据分析模块已就绪，请输入需要分析的数据集名称。",
            "reminder": f"已收到提醒请求。请设置提醒内容和时间。",
            "file_operation": "文件操作模块已激活，请告诉我您需要创建或读取的文件路径。",
            "report": "报告生成模块就绪，请指定报告类型和内容板块。",
            "status": "系统运行正常，所有模块在线。",
            "joke": self.jokes[hash(entities.get("city", "default")) % len(self.jokes)],
            "self_intro": "你好！我是 J.A.R.V.I.S. — Just A Rather Very Intelligent System。我是一个多功能智能Agent系统，可以帮助你处理天气查询、任务管理、数据分析、文件操作等多种任务。有什么可以帮你的吗？",
            "bye": "很高兴为你服务！随时回来找我聊天或工作。再见！",
            "crypto": f"检测到加密货币查询意图，置信度 {confidence:.2f}。正在为您查询 {entities.get('coin', '热门币种')} 的实时价格...",
            "exchange": f"检测到汇率查询意图，置信度 {confidence:.2f}。正在为您查询实时汇率...",
            "dictionary": f"好的，正在查询单词信息...",
            "holiday": f"正在查询公共节假日信息...",
            "book": f"正在搜索书籍信息...",
            "unknown": f"抱歉，我不太理解你的意思。你可以试试问我天气、查加密货币价格、查询汇率、查字典、查询节假日、搜索书籍、创建任务、或分析数据。",
        }

        response_text = responses.get(intent, responses["unknown"])

        # If sentiment is very negative, add empathy
        if sentiment.get("label") == "negative" and sentiment.get("score", 0) < -0.5:
            response_text = f"我注意到你可能不太开心 ({sentiment['label']})。让我来帮帮你：{response_text}"

        return {
            "intent": intent,
            "response": response_text,
            "action_needed": intent not in ["status", "joke", "self_intro", "bye"],
        }


# Singleton instance
nlp_processor = NLPProcessor()
