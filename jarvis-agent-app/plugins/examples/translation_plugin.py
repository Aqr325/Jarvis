"""
翻译插件示例
支持多语言翻译
"""

from typing import Any, Dict, List
import logging

from plugins.interface import (
    PluginInterface,
    PluginMetadata,
    PluginConfig,
    PluginCapability,
)
from plugins.base import PluginBase


logger = logging.getLogger(__name__)


class TranslationPlugin(PluginBase):
    """
    翻译插件
    
    支持：
    - 多语言互译
    - 自动语言检测
    - 翻译历史记录
    - 支持扩展翻译引擎
    """

    SUPPORTED_LANGUAGES = {
        "zh": "中文",
        "en": "English",
        "ja": "日本語",
        "ko": "한국어",
        "fr": "Français",
        "de": "Deutsch",
        "es": "Español",
        "ru": "Русский",
        "pt": "Português",
        "it": "Italiano",
    }

    # 简单的翻译字典（实际应该调用翻译 API）
    SIMPLE_TRANSLATIONS = {
        ("en", "zh"): {
            "hello": "你好",
            "world": "世界",
            "thank": "谢谢",
            "good": "好",
            "bad": "坏",
        },
        ("zh", "en"): {
            "你好": "hello",
            "世界": "world",
            "谢谢": "thank you",
            "好": "good",
            "坏": "bad",
        },
    }

    def __init__(self):
        super().__init__()
        self._translation_history: List[Dict[str, Any]] = []
        self._engine = "simple"  # simple, google, baidu, deepL

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Translation Plugin",
            version="1.0.0",
            author="JARVIS Team",
            description="多语言翻译插件，支持 10+ 种语言互译",
            capabilities=[PluginCapability.NLP_EXTENSION, PluginCapability.INTEGRATION],
            tags=["translation", "language", "nlp"],
            priority=20,
        )

    @property
    def config(self) -> PluginConfig:
        return PluginConfig(
            enabled=True,
            auto_load=False,
            config={
                "default_target_lang": "zh",
                "max_text_length": 1000,
                "engine": "simple",
            },
            timeout=15,
        )

    async def initialize(self) -> bool:
        logger.info("Initializing TranslationPlugin...")
        success = await super().initialize()
        if success:
            self._engine = self.config.config.get("engine", "simple")
            logger.info(f"TranslationPlugin initialized with engine: {self._engine}")
        return success

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行翻译
        
        Args:
            context: 包含 'text', 'target_lang', 'source_lang' 等键
        
        Returns:
            翻译结果
        """
        text = context.get("text", context.get("input", ""))
        target_lang = context.get("target_lang", self.config.config.get("default_target_lang", "zh"))
        source_lang = context.get("source_lang", "auto")
        
        if not text:
            return {
                "success": False,
                "error": "no_text",
                "message": "请提供要翻译的文本",
            }
        
        if len(text) > self.config.config.get("max_text_length", 1000):
            return {
                "success": False,
                "error": "text_too_long",
                "message": f"文本长度超过限制（最大 {self.config.config['max_text_length']} 字符）",
            }

        try:
            # 检测源语言（简单实现）
            if source_lang == "auto":
                source_lang = self._detect_language(text)
            
            # 执行翻译
            translated_text = await self._translate(text, source_lang, target_lang)
            
            # 记录历史
            self._record_history(text, source_lang, translated_text, target_lang)
            
            return {
                "success": True,
                "original_text": text,
                "translated_text": translated_text,
                "source_lang": source_lang,
                "source_lang_name": self.SUPPORTED_LANGUAGES.get(source_lang, source_lang),
                "target_lang": target_lang,
                "target_lang_name": self.SUPPORTED_LANGUAGES.get(target_lang, target_lang),
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "success": False,
                "error": "translation_error",
                "message": f"翻译失败: {str(e)}",
            }

    def _detect_language(self, text: str) -> str:
        """检测文本语言（简单实现）"""
        # 检测中文字符
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "zh"
        
        # 检测日文字符
        if any('\u3040' <= char <= '\u309f' for char in text):  # Hiragana
            return "ja"
        
        # 检测韩文字符
        if any('\uac00' <= char <= '\ud7af' for char in text):
            return "ko"
        
        # 默认英文
        return "en"

    async def _translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        执行翻译
        
        Args:
            text: 要翻译的文本
            source_lang: 源语言
            target_lang: 目标语言
        
        Returns:
            翻译后的文本
        """
        # 简单翻译引擎实现
        if self._engine == "simple":
            return self._simple_translate(text, source_lang, target_lang)
        
        # 未来可以扩展：
        # elif self._engine == "google":
        #     return await self._google_translate(text, source_lang, target_lang)
        # elif self._engine == "baidu":
        #     return await self._baidu_translate(text, source_lang, target_lang)
        # elif self._engine == "deepl":
        #     return await self._deepl_translate(text, source_lang, target_lang)
        
        return text  # 降级返回原文

    def _simple_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """简单翻译（基于字典）"""
        # 构建查找键
        lookup_key = (source_lang, target_lang)
        reverse_key = (target_lang, source_lang)
        
        # 尝试直接查找
        translation_dict = self.SIMPLE_TRANSLATIONS.get(lookup_key, {})
        
        # 逐词翻译
        words = text.split()
        translated_words = []
        
        for word in words:
            # 尝试精确匹配
            if word in translation_dict:
                translated_words.append(translation_dict[word])
            else:
                # 尝试模糊匹配（包含）
                found = False
                for key, value in translation_dict.items():
                    if key in word:
                        translated_words.append(word.replace(key, value))
                        found = True
                        break
                
                if not found:
                    translated_words.append(word)
        
        return " ".join(translated_words)

    def _record_history(self, original: str, source_lang: str, translated: str, target_lang: str):
        """记录翻译历史"""
        self._translation_history.append({
            "original_text": original,
            "source_lang": source_lang,
            "translated_text": translated,
            "target_lang": target_lang,
        })

    def get_tools(self) -> List[Dict[str, Any]]:
        """返回翻译工具"""
        return [
            {
                "name": "translate",
                "description": f"翻译文本，支持 {len(self.SUPPORTED_LANGUAGES)} 种语言",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要翻译的文本"
                        },
                        "target_lang": {
                            "type": "string",
                            "description": "目标语言代码",
                            "enum": list(self.SUPPORTED_LANGUAGES.keys())
                        },
                        "source_lang": {
                            "type": "string",
                            "description": "源语言代码（auto 为自动检测）"
                        }
                    },
                    "required": ["text", "target_lang"]
                }
            },
            {
                "name": "list_languages",
                "description": "列出所有支持的语言",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        return self.SUPPORTED_LANGUAGES.copy()

    async def shutdown(self) -> bool:
        logger.info("Shutting down TranslationPlugin...")
        self._translation_history.clear()
        return await super().shutdown()
