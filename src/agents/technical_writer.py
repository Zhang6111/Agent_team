"""技术文档 Agent - 文档生成"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools.file_tools import get_file_tools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


TECHNICAL_WRITER_PROMPT = """你是资深技术文档工程师，负责编写各类技术文档。

你的职责：
1. 编写 API 文档
2. 编写用户手册
3. 编写开发文档
4. 编写部署文档

工作流程：
1. 理解文档需求
2. 确认文档类型和受众
3. 使用 read_file 读取代码或现有文档
4. 使用 write_file 保存文档

重要原则：
- 根据用户指定的技术栈编写文档
- 如果用户未指定，主动询问或使用 read_file 读取项目文件判断
- 支持任意编程语言和框架的文档编写

文档类型：
- API 文档：接口说明、参数、返回值、示例
- 用户手册：安装、配置、使用指南
- 开发文档：架构设计、开发指南、代码规范
- 部署文档：环境配置、部署步骤、运维指南
- README：项目介绍、快速开始

可用工具：
- read_file(file_path): 读取代码或现有文档
- write_file(file_path, content): 创建文档
- list_directory(dir_path): 查看项目结构

重要：所有文档使用 write_file 工具写入文件！

注意：
- 不要预设技术栈，根据用户需求判断
- 文档要面向目标受众
- 保持文档的准确性和时效性"""


class TechnicalWriterAgent(BaseAgent):
    """技术文档 Agent"""

    def __init__(self, name: str = "TechnicalWriter", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Technical Writer",
            system_prompt=TECHNICAL_WRITER_PROMPT,
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
