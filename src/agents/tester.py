"""测试 Agent - 全场景功能测试"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
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
3. 编写测试用例
4. 执行测试
5. 输出测试报告

重要原则：
- 根据用户指定的技术栈选择测试框架
- 如果用户未指定，主动询问或根据项目文件判断
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
- read_file: 读取被测代码
- write_file: 创建测试文件
- list_directory: 列出测试目录
- run_command: 执行测试命令

输出格式：
```
# 测试报告

## 1. 测试概述
- 测试范围
- 测试环境
- 测试时间

## 2. 测试用例
| 用例 ID | 测试项 | 预期结果 | 实际结果 | 状态 |
|--------|--------|----------|----------|------|
| TC001  | ...    | ...      | ...      | PASS |

## 3. Bug 清单
| Bug ID | 严重程度 | 描述 | 状态 |
|--------|----------|------|------|

## 4. 测试结论
- 通过率
- 风险评估
- 建议
```

注意：
- 不要预设技术栈，根据用户需求或项目文件判断
- 使用工具执行测试
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
        )

        self.file_tools = FileTools()
        self.command_tools = CommandTools()
        message_bus.subscribe(self.name, self._handle_message)
        self._test_results: list[dict] = []

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

    def write_test_cases(self, code_content: str, prd_content: str = "") -> str:
        prompt = f"""请为以下代码编写测试用例：

【代码内容】
{code_content}

【需求内容】
{prd_content if prd_content else '无'}

请编写完整的测试用例，包括正常场景、边界条件和异常场景。"""
        test_cases = self.invoke(prompt)
        return test_cases

    def save_test_file(self, content: str, file_path: str) -> bool:
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 测试文件已保存到：{file_path}")
        return success

    def run_tests(self, test_file: str, cwd: Optional[str] = None) -> tuple[int, str]:
        command = f"pytest {test_file} -v"
        return self.command_tools.run_command_stream(command, cwd=cwd)

    def generate_test_report(self, test_results: list[dict]) -> str:
        report = f"""# 测试报告

## 1. 测试概述
- 测试用例总数：{len(test_results)}
- 通过：{sum(1 for r in test_results if r.get('status') == 'PASS')}
- 失败：{sum(1 for r in test_results if r.get('status') == 'FAIL')}

## 2. 测试结果详情
"""
        for result in test_results:
            status_icon = "✓" if result.get('status') == 'PASS' else "✗"
            report += f"### {status_icon} {result.get('name', 'Unknown')}\n"
            report += f"- 描述：{result.get('description', 'N/A')}\n\n"

        return report
