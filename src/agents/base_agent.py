"""Agent 基类 - 使用 LangChain Tool Calling"""
from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from src.config import settings
from src.memory import session_memory, SessionMemory
from src.mcp import embedded_mcp_client


class BaseAgent:
    """Agent 基类 - 支持 Tool Calling 和独立模型配置"""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: Optional[str] = None,
        memory: Optional[SessionMemory] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.memory = memory or session_memory

        config = settings.get_agent_config(name)
        if model:
            config["model"] = model
        
        self._model_name = config["model"]
        self.llm = ChatOpenAI(**config)

        self._tools = tools or []
        if self._tools:
            self.llm = self.llm.bind_tools(self._tools)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, role={self.role}, model={self._model_name})"

    def add_tool(self, tool: BaseTool) -> None:
        self._tools.append(tool)
        self.llm = self.llm.bind_tools(self._tools)

    def set_tools(self, tools: list[BaseTool]) -> None:
        self._tools = tools
        self.llm = self.llm.bind_tools(tools)

    def invoke(self, message: str, include_context: bool = True) -> str:
        if self._tools:
            return self._invoke_with_tools(message, include_context)
        return self._invoke_direct(message, include_context)

    def _invoke_with_tools(self, message: str, include_context: bool = True) -> str:
        context = ""
        if include_context:
            context = self.memory.to_context_prompt()

        full_input = message
        if context:
            full_input = f"【上下文】\n{context}\n\n【任务】\n{message}"

        messages = [SystemMessage(content=self.system_prompt)]
        messages.append(HumanMessage(content=full_input))

        response = self.llm.invoke(messages)

        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_results = []
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                try:
                    result = embedded_mcp_client.call_tool(tool_name, tool_args)
                    tool_results.append(f"\n[{tool_name}] 结果: {result}")
                except Exception as e:
                    tool_results.append(f"\n[{tool_name}] 错误: {e}")

            messages.append(response)
            messages.append(HumanMessage(content=f"工具执行结果: {' '.join(tool_results)}"))
            final_response = self.llm.invoke(messages)
            return final_response.content

        return response.content if hasattr(response, "content") else str(response)

    def _invoke_direct(self, message: str, include_context: bool = True) -> str:
        messages = [SystemMessage(content=self.system_prompt)]

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
        return response.content if hasattr(response, "content") else str(response)

    async def ainvoke(self, message: str, include_context: bool = True) -> str:
        return self.invoke(message, include_context)

    def invoke_with_history(self, message: str) -> str:
        messages = [SystemMessage(content=self.system_prompt)]
        messages.extend(self.memory.get_history())
        messages.append(HumanMessage(content=message))
        response = self.llm.invoke(messages)
        return response.content if hasattr(response, "content") else str(response)
