"""后端开发工程师 Agent"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 后端开发的系统提示词
BACKEND_DEV_PROMPT = """你是后端开发工程师，负责实现后端接口和业务逻辑。

你的职责：
1. 根据需求编写后端代码
2. 设计和实现 RESTful API
3. 处理数据库操作和数据存储
4. 实现业务逻辑和数据处理
5. 确保接口安全和性能

工作流程：
1. 接收任务：通过 MessageBus 接收项目总监派发的任务
2. 分析任务：理解需要实现的接口功能
3. 编写代码：创建后端文件
4. 返回结果：通过 MessageBus 发送完成通知

技术栈：
- 语言：Python/Node.js/Go/Java (根据项目需求)
- 框架：FastAPI/Django/Express/Spring
- 数据库：MySQL/PostgreSQL/MongoDB/Redis
- 认证：JWT/OAuth2

可用工具：
- read_file: 读取现有文件，了解项目结构
- write_file: 创建后端文件（API、模型、服务）
- append_file: 追加内容到现有文件
- file_exists: 检查文件是否存在
- create_directory: 创建目录结构
- list_directory: 列出目录内容，了解项目结构
- run_command: 执行 pip/npm/go 命令安装依赖或运行服务

输出要求：
- 提供完整的代码文件
- 包含必要的注释
- 说明 API 接口和使用方式
- 提供数据库设计（如需要）

注意：
- 使用工具创建文件，不要只输出代码
- 确保代码可运行
- 遵循项目规范
- 注意安全性"""


class BackendDeveloperAgent(BaseAgent):
    """
    后端开发工程师 Agent
    
    负责：
    - 实现后端接口和业务逻辑
    - 编写 API 代码
    """

    def __init__(self, name: str = "BackendDev", model: Optional[str] = None, memory=None):
        """
        初始化后端开发

        Args:
            name: Agent 名称
            model: 使用的模型名称
            memory: 记忆模块
        """
        super().__init__(
            name=name,
            role="Backend Developer",
            system_prompt=BACKEND_DEV_PROMPT,
            model=model,
            memory=memory,
        )

        # 工具实例
        self.file_tools = FileTools()
        self.command_tools = CommandTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)

    def _handle_message(self, message: Message) -> None:
        """处理接收到的 MCP 消息"""
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
            receiver=None,
            content=payload.model_dump(),
        )
        message_bus.publish_sync(message)

    def create_file(self, file_path: str, content: str) -> bool:
        """创建文件"""
        return self.file_tools.write_file(file_path, content)

    def read_file(self, file_path: str) -> str:
        """读取文件"""
        return self.file_tools.read_file(file_path)

    def run_command(self, command: str, timeout: Optional[int] = None) -> tuple[int, str]:
        """执行命令"""
        return self.command_tools.run_command_stream(command, timeout=timeout)
