"""Agent 基类 - 使用 LangChain Tool Calling"""
from typing import Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from src.config import settings
from src.memory import session_memory, SessionMemory


class BaseAgent:
    """Agent 基类 - 支持 Tool Calling 和独立模型配置"""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: Optional[str] = None,
        memory: Optional[SessionMemory] = None,
        tools: Optional[List[BaseTool]] = None,
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

    def set_tools(self, tools: List[BaseTool]) -> None:
        self._tools = tools
        self.llm = self.llm.bind_tools(tools)

    def invoke(self, message: str, include_context: bool = True) -> str:
        if self._tools:
            return self._invoke_with_tools(message, include_context)
        return self._invoke_direct(message, include_context)

    def _invoke_with_tools(self, message: str, include_context: bool = True) -> str:
        messages = [SystemMessage(content=self.system_prompt)]
        
        context = ""
        if include_context:
            context = self.memory.to_context_prompt()

        full_input = message
        if context:
            full_input = f"【上下文】\n{context}\n\n【任务】\n{message}"

        messages.append(HumanMessage(content=full_input))

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            response = self.llm.invoke(messages)

            if not hasattr(response, "tool_calls") or not response.tool_calls:
                return response.content if hasattr(response, "content") else str(response)

            messages.append(response)

            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", "")
                
                tool_result = self._execute_tool(tool_name, tool_args)
                
                messages.append(ToolMessage(
                    content=str(tool_result),
                    tool_call_id=tool_call_id
                ))

        return "达到最大迭代次数，任务可能未完成。"

    def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        for tool in self._tools:
            if tool.name == tool_name:
                try:
                    result = tool._run(**tool_args)
                    return result
                except Exception as e:
                    return f"工具执行错误: {e}"
        return f"未找到工具: {tool_name}"

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
