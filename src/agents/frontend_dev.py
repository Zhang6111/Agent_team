"""前端开发工程师 Agent"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 前端开发的系统提示词
FRONTEND_DEV_PROMPT = """你是前端开发工程师，负责实现前端页面和交互。

你的职责：
1. 根据需求编写 HTML/CSS/JavaScript 代码
2. 实现响应式页面设计
3. 确保跨浏览器兼容性
4. 优化前端性能
5. 遵循前端开发规范

技术栈：
- HTML5, CSS3, JavaScript (ES6+)
- 框架：React/Vue/Angular (根据项目需求)
- 样式：Tailwind CSS/Bootstrap/Sass
- 构建工具：Vite/Webpack

输出要求：
- 提供完整的代码文件
- 包含必要的注释
- 说明文件结构和运行方式

注意：
- 不要修改现有代码结构，除非得到明确授权
- 确保代码可运行
- 遵循项目规范"""


class FrontendDeveloperAgent(BaseAgent):
    """
    前端开发工程师 Agent
    
    负责：
    - 实现前端页面和交互
    - 编写 HTML/CSS/JavaScript 代码
    """

    def __init__(self, name: str = "FrontendDev", model: Optional[str] = None, memory=None):
        """
        初始化前端开发

        Args:
            name: Agent 名称
            model: 使用的模型名称
            memory: 记忆模块
        """
        super().__init__(
            name=name,
            role="Frontend Developer",
            system_prompt=FRONTEND_DEV_PROMPT,
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
