"""项目配置管理 - 支持每个 Agent 独立配置模型"""
import os
import re
import yaml
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def expand_env_vars(value):
    """展开环境变量引用，如 ${DEEPSEEK_API_KEY}"""
    if isinstance(value, str):
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, value)
        for match in matches:
            env_value = os.getenv(match, "")
            value = value.replace(f"${{{match}}}", env_value)
        return value
    return value


class Settings:
    """配置类 - 支持全局默认配置和 Agent 独立配置"""

    API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "deepseek-chat")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))

    _config: dict = {}
    _agent_configs: dict = {}
    _default_config: dict = {}

    @classmethod
    def load_config(cls):
        """加载配置文件"""
        config_path = Path(__file__).parent.parent.parent / "agents.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cls._config = yaml.safe_load(f) or {}
                cls._default_config = cls._config.get("default", {})
                cls._agent_configs = cls._config.get("agents", {})
        return cls._config

    @classmethod
    def get_agent_config(cls, agent_name: str) -> dict:
        """获取指定 Agent 的配置"""
        if not cls._config:
            cls.load_config()
        
        agent_config = cls._agent_configs.get(agent_name, {})
        
        api_key = expand_env_vars(agent_config.get("api_key")) or \
                  expand_env_vars(cls._default_config.get("api_key")) or \
                  cls.API_KEY
        
        base_url = expand_env_vars(agent_config.get("base_url")) or \
                   expand_env_vars(cls._default_config.get("base_url")) or \
                   cls.BASE_URL
        
        return {
            "model": agent_config.get("model", cls.DEFAULT_MODEL),
            "temperature": float(agent_config.get("temperature", cls.TEMPERATURE)),
            "max_tokens": int(agent_config.get("max_tokens", cls.MAX_TOKENS)),
            "base_url": base_url,
            "api_key": api_key,
        }

    @classmethod
    def get_all_agent_configs(cls) -> dict:
        """获取所有 Agent 配置"""
        if not cls._config:
            cls.load_config()
        return cls._agent_configs

    def validate(self) -> bool:
        if not self.API_KEY:
            raise ValueError("DEEPSEEK_API_KEY 未配置，请在 .env 文件中设置")
        return True

    @property
    def llm_config(self) -> dict:
        return {
            "model": self.DEFAULT_MODEL,
            "temperature": self.TEMPERATURE,
            "max_tokens": self.MAX_TOKENS,
            "base_url": self.BASE_URL,
            "api_key": self.API_KEY,
        }


settings = Settings()
