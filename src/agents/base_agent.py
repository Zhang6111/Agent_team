"""Agent 基类"""
from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import settings, SystemPrompts
from src.memory import session_memory, SessionMemory


class BaseAgent:
    """Agent 基类"""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: Optional[str] = None,
        memory: Optional[SessionMemory] = None,
    ):
        """
        初始化 Agent

        Args:
            name: Agent 名称
            role: 角色描述
            system_prompt: 系统提示词
            model: 使用的模型名称
            memory: 会话记忆实例
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.memory = memory or session_memory

        # 初始化 LLM
        config = settings.llm_config
        if model:
            config["model"] = model

        self.llm = ChatOpenAI(**config)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, role={self.role})"

    def invoke(self, message: str, include_context: bool = True) -> str:
        """
        调用 Agent 处理消息

        Args:
            message: 用户输入的消息
            include_context: 是否包含上下文

        Returns:
            Agent 的响应
        """
        # 构建消息
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        # 添加上下文（如果启用）
        if include_context:
            context = self.memory.to_context_prompt()
            if context:
                context_message = f"【当前上下文】\n{context}\n\n【用户消息】\n{message}"
                messages.append(HumanMessage(content=context_message))
            else:
                messages.append(HumanMessage(content=message))
        else:
            messages.append(HumanMessage(content=message))

        response = self.llm.invoke(messages)
        return response.content

    async def ainvoke(self, message: str, include_context: bool = True) -> str:
        """
        异步调用 Agent 处理消息

        Args:
            message: 用户输入的消息
            include_context: 是否包含上下文

        Returns:
            Agent 的响应
        """
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        if include_context:
            context = self.memory.to_context_prompt()
            if context:
                context_message = f"【当前上下文】\n{context}\n\n【用户消息】\n{message}"
                messages.append(HumanMessage(content=context_message))
            else:
                messages.append(HumanMessage(content=message))
        else:
            messages.append(HumanMessage(content=message))

        response = await self.llm.ainvoke(messages)
        return response.content

    def invoke_with_history(self, message: str) -> str:
        """
        带完整对话历史调用（用于多轮对话）

        Args:
            message: 用户输入的消息

        Returns:
            Agent 的响应
        """
        messages = [
            SystemMessage(content=self.system_prompt),
        ]
        
        # 添加所有历史消息
        messages.extend(self.memory.get_history())
        messages.append(HumanMessage(content=message))

        response = self.llm.invoke(messages)
        return response.content
