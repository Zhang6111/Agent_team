"""项目总监 Agent - 使用 MessageBus 真正派发任务"""
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base_agent import BaseAgent
from src.config import SystemPrompts
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload
from src.workflows import workflow_engine, Task, TaskType, TaskStatus


DIRECTOR_PROMPT = """你是一个项目总监，负责与用户直接沟通并协调团队完成项目。

你的职责：
1. 理解用户的项目需求和目标
2. 分析需求并制定项目计划
3. 协调团队成员完成各自任务
4. 向用户汇报项目进展和结果
5. 确保最终交付物符合用户期望

工作流程：
1. 分析用户需求，创建任务计划
2. 使用工作流引擎编排任务
3. 通过消息总线派发任务给团队成员
4. 收集结果并向用户汇报

重要规则：
- 所有代码修改必须谨慎，大规模重构前必须向用户确认
- 任务严格按工作流逐级派发
- 每个任务都要有明确的结果反馈

输出格式：
简洁清晰地汇报项目进展和结果。"""


class ProjectDirector(BaseAgent):
    """项目总监 Agent"""

    def __init__(self, model: Optional[str] = None, memory=None):
        super().__init__(
            name="ProjectDirector",
            role="Project Director",
            system_prompt=DIRECTOR_PROMPT,
            model=model,
            memory=memory,
        )

        self._team_members: dict[str, BaseAgent] = {}
        message_bus.subscribe(self.name, self._handle_message)

    def add_team_member(self, name: str, agent: BaseAgent) -> None:
        self._team_members[name] = agent
        message_bus.subscribe(name, self._handle_member_message)

    def get_team_member(self, name: str) -> Optional[BaseAgent]:
        return self._team_members.get(name)

    @property
    def team_members(self) -> list:
        return list(self._team_members.keys())

    def _handle_message(self, message: Message) -> None:
        if message.type == MessageType.RESPONSE:
            print(f"\n[任务完成] {message.sender}: 任务已完成")

    def _handle_member_message(self, message: Message) -> None:
        if message.type == MessageType.RESPONSE:
            payload = message.content
            if isinstance(payload, dict):
                print(f"\n[{message.sender}] 完成任务")

    def delegate_task(self, member_name: str, task: str, context: Optional[dict] = None) -> str:
        """委派任务给团队成员"""
        member = self.get_team_member(member_name)
        if not member:
            return f"团队成员 '{member_name}' 不存在"

        full_task = f"""
【任务来源】项目总监
【上下文】{context if context else '无'}
【任务内容】{task}

请直接执行任务并返回结果。
"""
        return member.invoke(full_task)

    def broadcast_task(self, task: str, receivers: Optional[list[str]] = None) -> None:
        """广播任务"""
        payload = TaskPayload(description=task)
        for receiver in (receivers or self.team_members):
            message = Message(
                type=MessageType.TASK,
                sender=self.name,
                receiver=receiver,
                content=payload.model_dump(),
            )
            message_bus.publish_sync(message)

    def create_and_execute_workflow(
        self,
        requirement: str,
        execute_callback: callable,
    ) -> str:
        """创建并执行工作流"""
        tasks = workflow_engine.create_tasks_from_requirement(requirement)

        results = workflow_engine.execute_workflow(execute_callback)

        summary = f"项目 '{requirement}' 已完成，共 {len(results)} 个任务\n\n"
        for r in results:
            status = "✅" if r["status"] == "completed" else "❌"
            summary += f"{status} {r['task_name']} ({r['assignee']}): {r.get('result', r.get('error', ''))}\n"

        return summary

    def invoke(self, message: str, include_context: bool = True) -> str:
        """调用 Director 处理用户需求"""
        context = ""
        if include_context:
            context = self.memory.to_context_prompt()

        full_input = message
        if context:
            full_input = f"【上下文】\n{context}\n\n【需求】\n{message}"

        if self._tools:
            return self._invoke_with_tools(full_input)
        return self._invoke_direct(full_input, include_context=False)

    def _invoke_with_tools(self, message: str) -> str:
        """使用工具调用"""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=message),
        ]

        response = self.llm.invoke(messages)

        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_results = []
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                try:
                    from src.mcp import embedded_mcp_client
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
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=message),
        ]
        response = self.llm.invoke(messages)
        return response.content if hasattr(response, "content") else str(response)
