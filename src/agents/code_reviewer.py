"""代码评审 Agent - 代码质量审查"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
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
3. 进行代码审查
4. 输出评审报告

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
- read_file: 读取被评审代码
- write_file: 创建评审报告
- list_directory: 查看项目结构

输出格式：
```
# 代码评审报告

## 1. 评审概述
- 评审范围
- 评审时间
- 代码统计

## 2. 问题列表
| 级别 | 文件 | 行号 | 问题描述 | 建议 |
|------|------|------|----------|------|
| 严重 | xxx | 10 | ... | ... |

## 3. 优点
## 4. 改进建议
## 5. 总结
```

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

    def review_code(self, code_content: str, file_path: str = "") -> str:
        prompt = f"""请评审以下代码：

【文件路径】{file_path}

【代码内容】
{code_content}

请输出完整的代码评审报告。"""
        return self.invoke(prompt)

    def save_report(self, content: str, file_path: str) -> bool:
        return self.file_tools.write_file(file_path, content)
