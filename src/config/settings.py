"""项目配置管理"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Settings:
    """配置类"""

    # DeepSeek API 配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # 默认模型
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "deepseek-chat")

    # 温度参数
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    # 最大 token 数
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))

    def validate(self) -> bool:
        """验证必要配置是否存在"""
        if not self.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY 未配置，请在 .env 文件中设置")
        return True

    @property
    def llm_config(self) -> dict:
        """返回 LLM 配置字典"""
        return {
            "model": self.DEFAULT_MODEL,
            "temperature": self.TEMPERATURE,
            "max_tokens": self.MAX_TOKENS,
            "base_url": self.DEEPSEEK_BASE_URL,
            "api_key": self.DEEPSEEK_API_KEY,
        }


settings = Settings()
