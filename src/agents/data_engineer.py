"""数据工程师 Agent - 数据库设计"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
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
4. 输出数据库设计文档

重要原则：
- 根据用户指定的数据库类型设计
- 如果用户未指定，主动询问或根据项目文件判断
- 支持任意类型的数据库

支持的数据库：
- 关系型：MySQL, PostgreSQL, SQLite, SQL Server, Oracle
- 文档型：MongoDB, CouchDB
- 键值型：Redis, Memcached
- 搜索引擎：Elasticsearch
- 时序数据库：InfluxDB, TimescaleDB
- 图数据库：Neo4j

可用工具：
- read_file: 读取现有设计或代码
- write_file: 创建数据库设计文档
- list_directory: 查看项目结构

输出格式：
```
# 数据库设计文档

## 1. 数据库概述
- 数据库类型
- 版本要求
- 连接配置

## 2. 数据模型
- ER 图（文字描述）
- 实体关系

## 3. 表结构设计
### 3.1 表名
| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|

## 4. 索引设计
## 5. 查询优化建议
## 6. 数据迁移脚本
```

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
        )

        self.file_tools = FileTools()
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

    def design_database(self, requirement: str) -> str:
        prompt = f"""请根据以下需求设计数据库：

【需求描述】
{requirement}

请输出完整的数据库设计文档。"""
        return self.invoke(prompt)

    def save_design(self, content: str, file_path: str) -> bool:
        return self.file_tools.write_file(file_path, content)
