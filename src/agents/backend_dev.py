"""后端开发工程师 Agent"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


BACKEND_DEV_PROMPT = """你是后端开发工程师，负责实现后端接口和业务逻辑。

你的职责：
1. 根据需求编写后端代码
2. 设计和实现 API 接口
3. 处理数据库操作和数据存储
4. 实现业务逻辑和数据处理
5. 确保接口安全和性能

工作流程：
1. 理解需要实现的功能
2. 确认技术栈（语言、框架、数据库等）
3. 编写代码并创建文件
4. 测试和优化

重要原则：
- 根据用户指定的技术栈开发（如：Java Spring Boot、Python FastAPI、Go Gin、Rust Actix 等）
- 如果用户未指定技术栈，主动询问或根据项目文件判断
- 支持任意编程语言和框架

支持的技术示例：
- Python: FastAPI, Django, Flask, Tornado
- Java: Spring Boot, Quarkus, Micronaut
- Node.js: Express, NestJS, Fastify, Koa
- Go: Gin, Echo, Fiber, Chi
- Rust: Actix-web, Axum, Warp
- C#: ASP.NET Core
- Ruby: Rails, Sinatra
- PHP: Laravel, Symfony

可用工具：
- read_file: 读取现有文件，了解项目结构
- write_file: 创建后端文件（API、模型、服务）
- append_file: 追加内容到现有文件
- file_exists: 检查文件是否存在
- create_directory: 创建目录结构
- list_directory: 列出目录内容
- run_command: 执行 pip/npm/go/cargo/maven 等命令

输出要求：
- 提供完整的代码文件
- 包含必要的注释
- 说明 API 接口和使用方式

注意：
- 不要预设技术栈，根据用户需求或项目文件判断
- 使用工具创建文件，不要只输出代码
- 确保代码可运行
- 注意安全性"""


class BackendDeveloperAgent(BaseAgent):
    """后端开发工程师 Agent"""

    def __init__(self, name: str = "BackendDev", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Backend Developer",
            system_prompt=BACKEND_DEV_PROMPT,
            model=model,
            memory=memory,
        )

        self.file_tools = FileTools()
        self.command_tools = CommandTools()
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

    def create_file(self, file_path: str, content: str) -> bool:
        return self.file_tools.write_file(file_path, content)

    def read_file(self, file_path: str) -> str:
        return self.file_tools.read_file(file_path)

    def run_command(self, command: str, timeout: Optional[int] = None) -> tuple[int, str]:
        return self.command_tools.run_command_stream(command, timeout=timeout)
