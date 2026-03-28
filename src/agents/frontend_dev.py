"""前端开发工程师 Agent"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools.file_tools import get_file_tools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


FRONTEND_DEV_PROMPT = """你是前端开发工程师，负责实现前端页面和交互。

你的职责：
1. 根据需求编写前端代码
2. 实现响应式页面设计
3. 确保跨浏览器兼容性
4. 优化前端性能
5. 遵循前端开发规范

工作流程：
1. 理解需要实现的功能
2. 确认技术栈（框架、样式方案等）
3. 使用 write_file 工具创建代码文件
4. 测试和优化

重要原则：
- 根据用户指定的技术栈开发（如：React、Vue、Angular、Flutter、SwiftUI、WPF 等）
- 如果用户未指定技术栈，主动询问或使用 read_file 读取项目文件判断
- 支持任意前端框架和技术

支持的技术示例：
- Web 前端：React, Vue, Angular, Svelte, Next.js, Nuxt.js
- 移动端：Flutter, React Native, SwiftUI, Jetpack Compose
- 桌面端：Electron, Tauri, WPF, WinUI
- 样式：Tailwind CSS, Bootstrap, Sass, CSS Modules, styled-components

可用工具：
- write_file(file_path, content): 创建文件
- read_file(file_path): 读取文件内容
- list_directory(dir_path): 列出目录内容
- create_directory(dir_path): 创建目录

重要：所有代码必须使用 write_file 工具写入文件，不要直接输出！

注意：
- 不要预设技术栈，根据用户需求或项目文件判断
- 使用工具创建文件，不要只输出代码
- 确保代码可运行"""


class FrontendDeveloperAgent(BaseAgent):
    """前端开发工程师 Agent"""

    def __init__(self, name: str = "FrontendDev", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Frontend Developer",
            system_prompt=FRONTEND_DEV_PROMPT,
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
