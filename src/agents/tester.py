"""测试 Agent - 全场景功能测试"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 测试 Agent 的系统提示词
TESTER_PROMPT = """你是专业测试工程师，负责全场景功能测试。

你的职责：
1. 根据需求和代码编写测试用例
2. 执行单元测试、集成测试
3. 发现并报告 bug
4. 输出测试报告
5. 确保代码质量

工作流程：
1. 接收任务：通过 MessageBus 接收项目总监派发的测试任务
2. 分析需求：理解需要测试的功能
3. 编写测试：创建测试文件
4. 执行测试：运行测试用例
5. 输出报告：通过 MessageBus 发送测试结果

可用工具：
- read_file: 读取被测代码，了解实现逻辑
- write_file: 创建测试文件
- list_directory: 列出测试目录
- run_command: 执行 pytest/jest 等测试命令

输出格式：
```
# 测试报告

## 1. 测试概述
- 测试范围
- 测试环境
- 测试时间

## 2. 测试用例
### 2.1 单元测试
| 用例 ID | 测试项 | 预期结果 | 实际结果 | 状态 |
|--------|--------|----------|----------|------|
| TC001  | ...    | ...      | ...      | PASS |

### 2.2 集成测试
...

## 3. Bug 清单
| Bug ID | 严重程度 | 描述 | 复现步骤 | 状态 |
|--------|----------|------|----------|------|
| BUG001 | High     | ...  | ...      | Open |

## 4. 测试结论
- 通过率
- 风险评估
- 建议
```

技术栈：
- Python: pytest, unittest
- JavaScript: Jest, Mocha
- API 测试：Postman, requests

注意：
- 使用工具执行测试，不要只输出测试代码
- 测试用例要覆盖边界条件
- Bug 描述要清晰、可复现"""


class TesterAgent(BaseAgent):
    """
    测试 Agent
    
    负责：
    - 编写测试用例
    - 执行测试
    - 输出测试报告
    """

    def __init__(self, name: str = "Tester", model: Optional[str] = None, memory=None):
        """
        初始化测试 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
            memory: 记忆模块
        """
        super().__init__(
            name=name,
            role="Test Engineer",
            system_prompt=TESTER_PROMPT,
            model=model,
            memory=memory,
        )

        # 工具实例
        self.file_tools = FileTools()
        self.command_tools = CommandTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)
        
        # 测试结果缓存
        self._test_results: list[dict] = []

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

    def write_test_cases(self, code_content: str, prd_content: str = "") -> str:
        """
        编写测试用例

        Args:
            code_content: 代码内容
            prd_content: PRD 内容（可选）

        Returns:
            测试用例代码
        """
        prompt = f"""
请为以下代码编写测试用例：

【代码内容】
{code_content}

【需求内容】
{prd_content if prd_content else '无'}

请使用 pytest 框架编写完整的测试用例，包括：
1. 正常场景测试
2. 边界条件测试
3. 异常场景测试
"""
        test_cases = self.invoke(prompt)
        return test_cases

    def save_test_file(self, content: str, file_path: str) -> bool:
        """
        保存测试文件

        Args:
            content: 测试代码内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 测试文件已保存到：{file_path}")
        return success

    def run_tests(self, test_file: str, cwd: Optional[str] = None) -> tuple[int, str]:
        """
        执行测试

        Args:
            test_file: 测试文件路径
            cwd: 工作目录

        Returns:
            (返回码，输出内容)
        """
        command = f"pytest {test_file} -v"
        return self.command_tools.run_command_stream(command, cwd=cwd)

    def generate_test_report(self, test_results: list[dict]) -> str:
        """
        生成测试报告

        Args:
            test_results: 测试结果列表

        Returns:
            测试报告
        """
        report = """# 测试报告

## 1. 测试概述
- 测试用例总数：{}
- 通过：{}
- 失败：{}
- 跳过：{}

## 2. 测试结果详情

""".format(
            len(test_results),
            sum(1 for r in test_results if r.get('status') == 'PASS'),
            sum(1 for r in test_results if r.get('status') == 'FAIL'),
            sum(1 for r in test_results if r.get('status') == 'SKIP'),
        )

        for result in test_results:
            status_icon = "✓" if result.get('status') == 'PASS' else "✗"
            report += f"### {status_icon} {result.get('name', 'Unknown')}\n"
            report += f"- 描述：{result.get('description', 'N/A')}\n"
            if result.get('status') == 'FAIL':
                report += f"- 错误：{result.get('error', 'N/A')}\n"
            report += "\n"

        # 结论
        pass_rate = sum(1 for r in test_results if r.get('status') == 'PASS') / len(test_results) * 100 if test_results else 0
        report += f"""## 3. 测试结论
- 通过率：{pass_rate:.1f}%
- 风险评估：{'低' if pass_rate >= 90 else '中' if pass_rate >= 70 else '高'}
- 建议：{'可以发布' if pass_rate >= 90 else '需要修复后重新测试'}
"""
        return report

    def find_bugs(self, code_content: str) -> list[dict]:
        """
        静态代码分析，查找潜在 bug

        Args:
            code_content: 代码内容

        Returns:
            Bug 列表
        """
        prompt = f"""
请分析以下代码，找出潜在的 bug 和问题：

【代码内容】
{code_content}

请列出所有发现的问题，包括：
1. 语法错误
2. 逻辑错误
3. 安全隐患
4. 性能问题
5. 代码规范问题

每个问题请说明：
- 问题描述
- 位置（行号）
- 严重程度（High/Medium/Low）
- 修复建议
"""
        response = self.invoke(prompt)
        # 简单解析，实际可以用更复杂的处理
        bugs = [{"description": response, "severity": "Medium"}]
        return bugs
