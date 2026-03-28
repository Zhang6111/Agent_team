"""前端开发工程师 Agent"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
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
3. 编写代码并创建文件
4. 测试和优化

重要原则：
- 根据用户指定的技术栈开发（如：React、Vue、Angular、Flutter、SwiftUI、WPF 等）
- 如果用户未指定技术栈，主动询问或根据项目文件判断
- 支持任意前端框架和技术

支持的技术示例：
- Web 前端：React, Vue, Angular, Svelte, Next.js, Nuxt.js
- 移动端：Flutter, React Native, SwiftUI, Jetpack Compose
- 桌面端：Electron, Tauri, WPF, WinUI
- 样式：Tailwind CSS, Bootstrap, Sass, CSS Modules, styled-components

可用工具：
- read_file: 读取现有文件，了解项目结构
- write_file: 创建前端文件（组件、页面、样式）
- append_file: 追加内容到现有文件
- file_exists: 检查文件是否存在
- create_directory: 创建目录结构
- list_directory: 列出目录内容
- run_command: 执行 npm/yarn/pnpm/flutter 等命令

输出要求：
- 提供完整的代码文件
- 包含必要的注释
- 说明文件结构和运行方式

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
