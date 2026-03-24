"""项目总监 Agent - 用户交互的唯一接口"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.config import SystemPrompts
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 项目总监的系统提示词
DIRECTOR_PROMPT = """你是一个项目总监，负责与用户直接沟通并协调团队完成项目。

你的职责：
1. 理解用户的项目需求和目标
2. 分析需求并制定项目计划
3. 协调团队成员完成各自任务
4. 向用户汇报项目进展和结果
5. 确保最终交付物符合用户期望

工作流程：
1. 分析用户需求
2. 制定执行计划
3. 如果需要创建/修改文件，输出 JSON 格式的操作指令
4. 向用户汇报结果

重要规则：
- 所有代码修改必须谨慎，大规模重构前必须向用户确认
- 任务严格逐级派发
- 每个任务都要有明确的结果反馈

输出格式要求：
你的回复必须包含两部分：
1. 文字说明 - 给用户看的分析和总结
2. JSON 操作指令 - 用 ```json 包裹，包含要执行的操作

JSON 格式示例：
```json
{
  "actions": [
    {"type": "create_file", "path": "backend/main.py", "content": "文件内容"},
    {"type": "create_file", "path": "backend/requirements.txt", "content": "依赖列表"}
  ],
  "message": "项目已创建完成"
}
```

操作类型：
- create_file: 创建文件（必须包含 path 和 content）
- modify_file: 修改文件（必须包含 path 和 content）
- run_command: 运行命令（必须包含 command）

注意事项：
- content 字段必须是文件的完整内容
- path 必须是相对路径，相对于工作目录
- 如果不需要执行操作，可以不包含 actions 字段"""


class ProjectDirector(BaseAgent):
    """
    项目总监 Agent
    
    这是用户直接交互的唯一接口，负责：
    - 理解用户需求
    - 协调团队完成任务
    - 反馈最终结果
    """

    def __init__(self, model: Optional[str] = None, memory=None):
        """
        初始化项目总监

        Args:
            model: 使用的模型名称，默认使用配置中的 DEFAULT_MODEL
            memory: 会话记忆实例
        """
        super().__init__(
            name="ProjectDirector",
            role="Project Director",
            system_prompt=DIRECTOR_PROMPT,
            model=model,
            memory=memory,
        )

        # 内部团队成员（后续实现）
        self._team_members: dict[str, BaseAgent] = {}
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)

    def add_team_member(self, name: str, agent: BaseAgent) -> None:
        """
        添加团队成员

        Args:
            name: 成员名称
            agent: Agent 实例
        """
        self._team_members[name] = agent

    def get_team_member(self, name: str) -> Optional[BaseAgent]:
        """
        获取团队成员

        Args:
            name: 成员名称

        Returns:
            对应的 Agent，如果不存在则返回 None
        """
        return self._team_members.get(name)

    @property
    def team_members(self) -> list:
        """获取所有团队成员名称"""
        return list(self._team_members.keys())

    def delegate_task(self, member_name: str, task: str, context: Optional[dict] = None) -> str:
        """
        委派任务给团队成员

        Args:
            member_name: 成员名称
            task: 任务描述
            context: 上下文信息

        Returns:
            成员的响应
        """
        member = self.get_team_member(member_name)
        if not member:
            return f"团队成员 '{member_name}' 不存在"
        
        # 构建任务上下文
        full_task = f"""
【任务来源】项目总监
【上下文】{context if context else '无'}
【任务内容】{task}

请直接执行任务并返回结果。
"""
        return member.invoke(full_task)

    def _handle_message(self, message: Message) -> None:
        """
        处理接收到的 MCP 消息

        Args:
            message: 接收到的消息
        """
        if message.type == MessageType.RESPONSE:
            # 处理任务完成响应
            payload = message.content
            if isinstance(payload, ResponsePayload):
                print(f"\n[任务完成] {message.sender}: {'成功' if payload.success else '失败'}")

    def broadcast_task(self, task: str, receivers: Optional[list[str]] = None) -> None:
        """
        广播任务给多个成员

        Args:
            task: 任务描述
            receivers: 接收者列表，None 表示广播给所有人
        """
        payload = TaskPayload(description=task)
        for receiver in (receivers or self.team_members):
            message = Message(
                type=MessageType.TASK,
                sender=self.name,
                receiver=receiver,
                content=payload.model_dump(),
            )
            message_bus.publish_sync(message)
