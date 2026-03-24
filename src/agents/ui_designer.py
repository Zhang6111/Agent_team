"""UI 设计 Agent - 页面布局、样式、交互规范"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# UI 设计 Agent 的系统提示词
UI_DESIGNER_PROMPT = """你是专业 UI/UX 设计师，负责页面布局、样式和交互规范。

你的职责：
1. 根据 PRD 设计页面布局和视觉风格
2. 输出 UI 设计规范和组件库
3. 设计交互流程和用户体验
4. 确保设计的一致性和可访问性
5. 提供前端可用的样式代码

输出格式：
```
# UI 设计规范

## 1. 设计风格
- 色彩方案（主色、辅色、强调色）
- 字体规范
- 图标风格

## 2. 布局规范
- 栅格系统
- 间距规范
- 响应式断点

## 3. 组件库
### 3.1 基础组件
- 按钮
- 输入框
- 卡片
- ...

### 3.2 复合组件
- 导航栏
- 表单
- 列表
- ...

## 4. 交互规范
- 动画效果
- 过渡效果
- 反馈机制

## 5. 页面设计
### 5.1 页面列表
### 5.2 页面布局说明

## 6. 样式代码
```css
/* 核心样式变量 */
:root {
  --primary-color: #xxx;
  ...
}
```
```

注意：
- 设计要美观、现代
- 考虑可访问性（无障碍）
- 提供可用的 CSS/Tailwind 代码"""


class UIDesignerAgent(BaseAgent):
    """
    UI 设计 Agent
    
    负责：
    - 页面布局设计
    - 样式规范输出
    - 交互设计
    """

    def __init__(self, name: str = "UIDesigner", model: Optional[str] = None):
        """
        初始化 UI 设计 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
        """
        super().__init__(
            name=name,
            role="UI/UX Designer",
            system_prompt=UI_DESIGNER_PROMPT,
            model=model,
        )

        # 工具实例
        self.file_tools = FileTools()
        
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

    def design_ui(self, prd_content: str, page_type: str = "web") -> str:
        """
        根据 PRD 设计 UI

        Args:
            prd_content: PRD 文档内容
            page_type: 页面类型（web/mobile）

        Returns:
            UI 设计规范文档
        """
        prompt = f"""
请根据以下 PRD 设计 UI 规范：

【PRD 内容】
{prd_content}

【页面类型】{page_type}

请输出完整的 UI 设计规范，包括：
1. 色彩方案（主色、辅色、强调色，提供 hex 值）
2. 字体规范（字号、字重、行高）
3. 布局规范（栅格、间距）
4. 核心组件样式
5. 提供 CSS/Tailwind 样式代码
"""
        design = self.invoke(prompt)
        return design

    def generate_color_palette(self, style: str = "modern") -> dict:
        """
        生成色彩方案

        Args:
            style: 风格类型

        Returns:
            色彩方案字典
        """
        prompt = f"""
请为{style}风格的设计生成色彩方案。

请提供：
- 主色 (Primary)
- 辅色 (Secondary)
- 强调色 (Accent)
- 成功色 (Success)
- 警告色 (Warning)
- 错误色 (Error)
- 中性色 (Neutral grays)

每个颜色提供 hex 值和 RGB 值。
"""
        response = self.invoke(prompt)
        return {"palette": response}

    def generate_component_code(self, component_name: str, style_framework: str = "tailwind") -> str:
        """
        生成组件样式代码

        Args:
            component_name: 组件名称
            style_framework: 样式框架（tailwind/css/styled-components）

        Returns:
            组件样式代码
        """
        prompt = f"""
请为"{component_name}"组件生成{style_framework}样式代码。

要求：
1. 包含所有状态（default, hover, active, disabled）
2. 响应式设计
3. 可访问性支持
4. 包含使用示例
"""
        code = self.invoke(prompt)
        return code

    def save_design(self, content: str, file_path: str) -> bool:
        """
        保存设计文档

        Args:
            content: 设计文档内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 设计文档已保存到：{file_path}")
        return success

    def generate_css_variables(self, design_tokens: dict) -> str:
        """
        生成 CSS 变量

        Args:
            design_tokens: 设计变量

        Returns:
            CSS 变量代码
        """
        css = ":root {\n"
        for key, value in design_tokens.items():
            css += f"  --{key}: {value};\n"
        css += "}\n"
        return css
