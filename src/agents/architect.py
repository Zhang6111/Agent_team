"""架构师 Agent - 技术架构设计"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools.file_tools import get_file_tools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


ARCHITECT_PROMPT = """你是资深架构师，负责设计项目整体技术架构。

你的职责：
1. 根据 PRD 设计技术架构方案
2. 定义项目目录结构和规范
3. 设计技术选型和接口标准
4. 输出架构设计文档
5. 指导研发团队实现架构

工作流程：
1. 理解项目规模和技术要求
2. 根据用户指定的语言/框架设计架构
3. 使用 write_file 工具保存架构设计文档
4. 定义项目结构和规范

重要原则：
- 根据用户指定的技术栈设计架构（如：Java Spring Boot、Python FastAPI、Go Gin、Rust Actix 等）
- 如果用户未指定技术栈，主动询问或使用 read_file 读取项目文件判断
- 支持任意编程语言和框架
- 架构要可扩展、可维护

可用工具：
- write_file(file_path, content): 创建架构设计文档
- read_file(file_path): 读取需求文档或现有代码
- list_directory(dir_path): 查看项目结构

重要：所有文档必须使用 write_file 工具写入文件！

注意：
- 不要预设技术栈，根据用户需求或项目文件判断
- 架构要可扩展、可维护
- 技术选型要合理、成熟
- 考虑安全性和性能"""


class ArchitectAgent(BaseAgent):
    """架构师 Agent - 负责技术架构设计"""

    def __init__(self, name: str = "Architect", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Software Architect",
            system_prompt=ARCHITECT_PROMPT,
            model=model,
            memory=memory,
            tools=get_file_tools(),
        )

        message_bus.subscribe(self.name, self._handle_message)

    def _handle_message(self, message: Message) -> None:
        if message.type == MessageType.TASK and message.receiver == self.name:
            payload = message.content
            if isinstance(payload, dict):
                task_payload = TaskPayload(**payload)
                print(f"\n[新任务] {self.name} 收到：{task_payload.description}")

    def send_response(
        self,
        task_id: str,
        success: bool,
        result: any = None,
        error_message: Optional[str] = None,
    ) -> None:
        payload = ResponsePayload(
            task_id=task_id,
            success=success,
            result=result,
            error_message=error_message,
        )
        message = Message(
            type=MessageType.RESPONSE,
            sender=self.name,
            receiver=None,
            content=payload.model_dump(),
        )
        message_bus.publish_sync(message)
