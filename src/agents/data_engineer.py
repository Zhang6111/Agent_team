"""数据工程师 Agent - 数据库设计"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools.file_tools import get_file_tools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


DATA_ENGINEER_PROMPT = """你是资深数据工程师，负责数据库设计和数据处理。

你的职责：
1. 设计数据库模型
2. 设计数据表结构
3. 编写数据处理逻辑
4. 优化数据查询性能

工作流程：
1. 理解数据需求
2. 确认数据库类型
3. 设计数据模型
4. 使用 write_file 保存数据库设计文档

重要原则：
- 根据用户指定的数据库类型设计
- 如果用户未指定，主动询问或使用 read_file 读取项目文件判断
- 支持任意类型的数据库

支持的数据库：
- 关系型：MySQL, PostgreSQL, SQLite, SQL Server, Oracle
- 文档型：MongoDB, CouchDB
- 键值型：Redis, Memcached
- 搜索引擎：Elasticsearch
- 时序数据库：InfluxDB, TimescaleDB
- 图数据库：Neo4j

可用工具：
- read_file(file_path): 读取现有设计或代码
- write_file(file_path, content): 创建数据库设计文档
- list_directory(dir_path): 查看项目结构

重要：数据库设计文档使用 write_file 工具写入文件！

注意：
- 不要预设数据库类型，根据用户需求判断
- 设计要考虑性能和扩展性"""


class DataEngineerAgent(BaseAgent):
    """数据工程师 Agent"""

    def __init__(self, name: str = "DataEngineer", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Data Engineer",
            system_prompt=DATA_ENGINEER_PROMPT,
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
