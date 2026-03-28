"""架构师 Agent - 技术架构设计"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
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
3. 输出架构设计文档
4. 定义项目结构和规范

重要原则：
- 根据用户指定的技术栈设计架构（如：Java Spring Boot、Python FastAPI、Go Gin 等）
- 如果用户未指定技术栈，主动询问或根据项目文件判断
- 支持任意编程语言和框架
- 架构要可扩展、可维护

输出格式（架构设计文档模板）：
```
# 架构设计文档

## 1. 架构概述
- 架构图（文字描述）
- 核心组件
- 数据流向

## 2. 技术选型
### 2.1 编程语言
### 2.2 框架
### 2.3 数据库
### 2.4 中间件

## 3. 项目结构
```
project/
├── src/
├── tests/
├── docs/
└── ...
```

## 4. 接口设计
### 4.1 API 规范
### 4.2 核心接口列表

## 5. 数据设计
### 5.1 数据模型
### 5.2 数据库表结构

## 6. 安全设计
## 7. 性能设计
```

可用工具：
- read_file: 读取需求文档或现有代码
- write_file: 创建架构设计文档
- file_exists: 检查文件是否存在
- list_directory: 列出目录结构

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
        )

        self.file_tools = FileTools()
        message_bus.subscribe(self.name, self._handle_message)
        self._architecture_cache: dict[str, str] = {}

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

    def design_architecture(self, prd_content: str) -> str:
        prompt = f"""请根据以下 PRD 设计技术架构：

【PRD 内容】
{prd_content}

请输出完整的架构设计文档。"""
        architecture = self.invoke(prompt)
        return architecture

    def save_architecture(self, content: str, file_path: str) -> bool:
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 架构设计已保存到：{file_path}")
        return success
