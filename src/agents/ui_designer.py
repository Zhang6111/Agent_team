"""UI 设计师 Agent - 界面设计"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools.file_tools import get_file_tools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


UI_DESIGNER_PROMPT = """你是资深 UI 设计师，负责用户界面设计。

你的职责：
1. 设计用户界面布局
2. 定义视觉规范和样式
3. 输出设计稿和设计文档
4. 确保用户体验

工作流程：
1. 理解设计需求
2. 确认平台和技术栈
3. 设计界面方案
4. 使用 write_file 保存设计文档

重要原则：
- 根据用户指定的平台设计（Web、移动端、桌面端等）
- 如果用户未指定，主动询问
- 支持任意平台和框架的 UI 设计

支持的平台：
- Web：响应式设计、移动优先
- 移动端：iOS (SwiftUI)、Android (Jetpack Compose)、Flutter
- 桌面端：Electron、Tauri、WPF、WinUI
- 小程序：微信、支付宝、抖音

可用工具：
- read_file(file_path): 读取现有设计或代码
- write_file(file_path, content): 创建设计文档
- list_directory(dir_path): 查看项目结构

重要：设计文档使用 write_file 工具写入文件！

注意：
- 不要预设平台，根据用户需求判断
- 设计要考虑实现可行性"""


class UIDesignerAgent(BaseAgent):
    """UI 设计师 Agent"""

    def __init__(self, name: str = "UIDesigner", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="UI Designer",
            system_prompt=UI_DESIGNER_PROMPT,
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
