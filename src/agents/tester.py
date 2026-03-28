"""测试 Agent - 全场景功能测试"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools.file_tools import get_file_tools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


TESTER_PROMPT = """你是专业测试工程师，负责全场景功能测试。

你的职责：
1. 根据需求和代码编写测试用例
2. 执行单元测试、集成测试
3. 发现并报告 bug
4. 输出测试报告
5. 确保代码质量

工作流程：
1. 理解需要测试的功能
2. 确认技术栈和测试框架
3. 使用 write_file 工具创建测试文件
4. 输出测试报告

重要原则：
- 根据用户指定的技术栈选择测试框架
- 如果用户未指定，主动询问或使用 read_file 读取项目文件判断
- 支持任意编程语言的测试

支持的测试框架示例：
- Python: pytest, unittest, nose
- JavaScript: Jest, Mocha, Vitest
- Java: JUnit, TestNG
- Go: testing, testify
- Rust: cargo test
- C#: xUnit, NUnit, MSTest
- Ruby: RSpec, Minitest

可用工具：
- write_file(file_path, content): 创建测试文件
- read_file(file_path): 读取被测代码
- list_directory(dir_path): 列出目录内容

重要：所有测试文件必须使用 write_file 工具写入文件！

注意：
- 不要预设技术栈，根据用户需求或项目文件判断
- 测试用例要覆盖边界条件"""


class TesterAgent(BaseAgent):
    """测试 Agent"""

    def __init__(self, name: str = "Tester", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Test Engineer",
            system_prompt=TESTER_PROMPT,
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
