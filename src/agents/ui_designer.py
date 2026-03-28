"""UI 设计师 Agent - 界面设计"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
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
4. 输出设计文档

重要原则：
- 根据用户指定的平台设计（Web、移动端、桌面端等）
- 如果用户未指定，主动询问
- 支持任意平台和框架的 UI 设计

支持的平台：
- Web：响应式设计、移动优先
- 移动端：iOS (SwiftUI)、Android (Jetpack Compose)、Flutter
- 桌面端：Electron、Tauri、WPF、WinUI
- 小程序：微信、支付宝、抖音

设计输出：
- 布局结构
- 组件规范
- 颜色方案
- 字体规范
- 间距规范
- 交互说明

可用工具：
- read_file: 读取现有设计或代码
- write_file: 创建设计文档
- list_directory: 查看项目结构

输出格式：
```
# UI 设计文档

## 1. 设计概述
- 设计目标
- 目标用户
- 设计风格

## 2. 页面结构
- 页面列表
- 导航结构
- 信息架构

## 3. 视觉规范
### 3.1 颜色
### 3.2 字体
### 3.3 图标
### 3.4 间距

## 4. 组件设计
## 5. 交互说明
## 6. 响应式适配
```

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

    def design_ui(self, requirement: str) -> str:
        prompt = f"""请根据以下需求设计 UI：

【需求描述】
{requirement}

请输出完整的 UI 设计文档。"""
        return self.invoke(prompt)

    def save_design(self, content: str, file_path: str) -> bool:
        return self.file_tools.write_file(file_path, content)
