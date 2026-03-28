"""代码评审 Agent - 代码质量审查"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools.file_tools import get_file_tools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


CODE_REVIEWER_PROMPT = """你是资深代码评审专家，负责审查代码质量。

你的职责：
1. 审查代码质量和规范性
2. 发现潜在问题和风险
3. 提出改进建议
4. 输出代码评审报告

工作流程：
1. 理解需要评审的代码
2. 确认编程语言和规范
3. 使用 read_file 读取代码
4. 使用 write_file 保存评审报告

重要原则：
- 根据用户指定的编程语言进行评审
- 如果用户未指定，根据代码文件判断
- 支持任意编程语言的代码评审

评审要点：
- 代码规范：命名、格式、注释
- 代码质量：可读性、可维护性、可扩展性
- 潜在问题：逻辑错误、边界条件、异常处理
- 安全隐患：注入、越权、敏感信息
- 性能问题：算法复杂度、资源泄漏
- 最佳实践：设计模式、SOLID 原则

可用工具：
- read_file(file_path): 读取被评审代码
- write_file(file_path, content): 创建评审报告
- list_directory(dir_path): 查看项目结构

重要：评审报告使用 write_file 工具写入文件！

注意：
- 不要预设编程语言，根据代码内容判断
- 问题要具体、可操作
- 建议要合理、可行"""


class CodeReviewerAgent(BaseAgent):
    """代码评审 Agent"""

    def __init__(self, name: str = "CodeReviewer", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Code Reviewer",
            system_prompt=CODE_REVIEWER_PROMPT,
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
