"""Agent 基类"""
from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import settings, SystemPrompts


class BaseAgent:
    """Agent 基类"""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: Optional[str] = None,
    ):
        """
        初始化 Agent

        Args:
            name: Agent 名称
            role: 角色描述
            system_prompt: 系统提示词
            model: 使用的模型名称
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt

        # 初始化 LLM
        config = settings.llm_config
        if model:
            config["model"] = model

        self.llm = ChatOpenAI(**config)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, role={self.role})"

    def invoke(self, message: str) -> str:
        """
        调用 Agent 处理消息

        Args:
            message: 用户输入的消息

        Returns:
            Agent 的响应
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=message),
        ]
        response = self.llm.invoke(messages)
        return response.content

    async def ainvoke(self, message: str) -> str:
        """
        异步调用 Agent 处理消息

        Args:
            message: 用户输入的消息

        Returns:
            Agent 的响应
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=message),
        ]
        response = await self.llm.ainvoke(messages)
        return response.content
