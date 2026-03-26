"""研发效能组长 Agent - 统筹开发任务"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.config import SystemPrompts
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 研发效能组长的系统提示词
TECH_LEAD_PROMPT = """你是研发效能组长，负责统筹和管理开发任务。

你的职责：
1. 接收项目总监分发的开发任务
2. 分析任务并分解为前端/后端子任务
3. 分配任务给前端开发组和后端开发组
4. 跟踪开发进度，确保按时交付
5. 进行代码审查和技术指导
6. 整合开发结果并反馈给项目总监

技能要求：
- 精通前后端开发技术栈
- 具备良好的任务分解和分配能力
- 能够进行代码审查和质量把控

工作流程：
1. 接收任务：通过 MessageBus 接收项目总监派发的任务
2. 分析需求：理解需要实现的功能
3. 分配任务：将任务分解并分配给前端/后端开发
4. 跟踪进度：等待开发完成
5. 整合结果：汇总前后端代码返回给项目总监

可用工具：
- read_file: 读取现有代码，了解项目结构
- write_file: 创建任务文档或配置文件
- list_directory: 列出目录内容，了解项目结构
- run_command: 执行构建命令

注意：
- 使用 MessageBus 与团队成员通信
- 及时汇报进度
- 确保代码符合规范"""


class TechLeadAgent(BaseAgent):
    """
    研发效能组长 Agent
    
    负责：
    - 接收项目总监的开发任务
    - 分解并分配给前端/后端开发组
    - 整合开发结果
    """

    def __init__(self, model: Optional[str] = None, memory=None):
        """
        初始化研发效能组长

        Args:
            model: 使用的模型名称
            memory: 会话记忆实例
        """
        super().__init__(
            name="TechLead",
            role="Tech Lead",
            system_prompt=TECH_LEAD_PROMPT,
            model=model,
            memory=memory,
        )

        # 下属开发组
        self._frontend_devs: dict[str, BaseAgent] = {}
        self._backend_devs: dict[str, BaseAgent] = {}
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)

    def add_frontend_dev(self, name: str, agent: BaseAgent) -> None:
        """添加前端开发"""
        self._frontend_devs[name] = agent

    def add_backend_dev(self, name: str, agent: BaseAgent) -> None:
        """添加后端开发"""
        self._backend_devs[name] = agent

    @property
    def frontend_devs(self) -> list:
        """获取所有前端开发名称"""
        return list(self._frontend_devs.keys())

    @property
    def backend_devs(self) -> list:
        """获取所有后端开发名称"""
        return list(self._backend_devs.keys())

    def assign_frontend_task(
        self, dev_name: str, task: str, context: Optional[dict] = None
    ) -> str:
        """分配前端任务"""
        dev = self._frontend_devs.get(dev_name)
        if not dev:
            return f"前端开发 '{dev_name}' 不存在"
        
        full_task = f"""
【任务来源】研发效能组长
【上下文】{context if context else '无'}
【任务内容】{task}

请执行前端开发任务并返回代码和说明。
"""
        return dev.invoke(full_task)

    def assign_backend_task(
        self, dev_name: str, task: str, context: Optional[dict] = None
    ) -> str:
        """分配后端任务"""
        dev = self._backend_devs.get(dev_name)
        if not dev:
            return f"后端开发 '{dev_name}' 不存在"
        
        full_task = f"""
【任务来源】研发效能组长
【上下文】{context if context else '无'}
【任务内容】{task}

请执行后端开发任务并返回代码和说明。
"""
        return dev.invoke(full_task)

    def _handle_message(self, message: Message) -> None:
        """处理接收到的 MCP 消息"""
        if message.type == MessageType.TASK and message.receiver == self.name:
            # 接收新任务
            payload = message.content
            if isinstance(payload, dict):
                task_payload = TaskPayload(**payload)
                print(f"\n[新任务] 来自 {message.sender}: {task_payload.description}")

    def send_response(
        self,
        task_id: str,
        success: bool,
        result: any = None,
        error_message: Optional[str] = None,
    ) -> None:
        """发送任务响应"""
        payload = ResponsePayload(
            task_id=task_id,
            success=success,
            result=result,
            error_message=error_message,
        )
        message = Message(
            type=MessageType.RESPONSE,
            sender=self.name,
            receiver=None,  # 广播
            content=payload.model_dump(),
        )
        message_bus.publish_sync(message)
