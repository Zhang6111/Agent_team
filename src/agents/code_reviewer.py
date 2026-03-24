"""代码评审 Agent - 代码审查、规范检查、重构建议"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 代码评审 Agent 的系统提示词
CODE_REVIEWER_PROMPT = """你是资深代码评审专家，负责代码审查和规范检查。

你的职责：
1. 审查代码质量和规范
2. 发现潜在 bug 和问题
3. 提出优化建议
4. 确保代码可维护性
5. 拦截违规重构

评审维度：
- 代码规范（命名、格式、注释）
- 代码质量（复杂度、重复度）
- 安全性（漏洞、敏感信息）
- 性能（效率、资源使用）
- 可测试性（单元测试覆盖）
- 可维护性（模块化、解耦）

输出格式：
```
# 代码评审报告

## 1. 评审概述
- 评审文件
- 评审时间
- 总体评分

## 2. 问题清单
### 2.1 严重问题
| 位置 | 问题描述 | 建议 |
|------|----------|------|

### 2.2 一般问题
...

### 2.3 建议改进
...

## 3. 代码规范检查
- 命名规范
- 格式规范
- 注释规范

## 4. 安全性检查
- SQL 注入风险
- XSS 风险
- 敏感信息泄露

## 5. 性能建议
- 时间复杂度
- 空间复杂度
- 优化建议

## 6. 评审结论
- 是否通过
- 需要修改的问题
- 后续建议
```

注意：
- 问题描述要具体（文件 + 行号）
- 建议要可执行
- 大规模重构需要项目总监授权"""


class CodeReviewerAgent(BaseAgent):
    """
    代码评审 Agent
    
    负责：
    - 代码审查
    - 规范检查
    - 重构建议
    """

    def __init__(self, name: str = "CodeReviewer", model: Optional[str] = None):
        """
        初始化代码评审 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
        """
        super().__init__(
            name=name,
            role="Code Reviewer",
            system_prompt=CODE_REVIEWER_PROMPT,
            model=model,
        )

        # 工具实例
        self.file_tools = FileTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)
        
        # 评审记录
        self._review_history: list[dict] = []

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

    def review_code(self, code_content: str, file_path: str = "") -> str:
        """
        评审代码

        Args:
            code_content: 代码内容
            file_path: 文件路径

        Returns:
            评审报告
        """
        prompt = f"""
请评审以下代码：

【文件】{file_path if file_path else '未知'}

【代码内容】
{code_content}

请从以下维度进行评审：
1. 代码规范（命名、格式、注释）
2. 代码质量（复杂度、重复度）
3. 安全性（漏洞、敏感信息）
4. 性能（效率、资源使用）
5. 可测试性
6. 可维护性

请输出详细的评审报告，包括问题位置和修改建议。
"""
        review = self.invoke(prompt)
        self._review_history.append({
            "file": file_path,
            "review": review,
        })
        return review

    def review_file(self, file_path: str) -> str:
        """
        评审文件

        Args:
            file_path: 文件路径

        Returns:
            评审报告
        """
        try:
            code = self.file_tools.read_file(file_path)
            return self.review_code(code, file_path)
        except Exception as e:
            return f"评审失败：{e}"

    def check_code_style(self, code_content: str, language: str = "python") -> dict:
        """
        检查代码风格

        Args:
            code_content: 代码内容
            language: 编程语言

        Returns:
            风格检查结果
        """
        prompt = f"""
请检查以下{language}代码的风格规范：

{code_content}

检查项：
1. 命名规范（变量、函数、类）
2. 格式规范（缩进、空行、行宽）
3. 注释规范（文档字符串、行注释）
4. 导入规范

请以 JSON 格式返回检查结果：
{{
    "passed": bool,
    "issues": [
        {{"line": int, "type": str, "message": str}}
    ]
}}
"""
        response = self.invoke(prompt)
        return {"result": response}

    def detect_smells(self, code_content: str) -> list[dict]:
        """
        检测代码异味

        Args:
            code_content: 代码内容

        Returns:
            代码异味列表
        """
        prompt = f"""
请检测以下代码中的代码异味（Code Smells）：

{code_content}

常见的代码异味：
- 过长的函数/类
- 重复代码
- 过多的参数
- 过深的嵌套
- 不恰当的命名
- 过多的注释（可能说明代码不清晰）
- 未使用的变量/导入

请列出所有发现的问题。
"""
        response = self.invoke(prompt)
        return [{"description": response}]

    def suggest_refactoring(self, code_content: str) -> str:
        """
        提供重构建议

        Args:
            code_content: 代码内容

        Returns:
            重构建议
        """
        prompt = f"""
请为以下代码提供重构建议：

{code_content}

请说明：
1. 需要重构的原因
2. 重构的具体方案
3. 重构后的代码示例
4. 重构带来的好处

注意：大规模重构需要谨慎，确保不破坏现有功能。
"""
        suggestion = self.invoke(prompt)
        return suggestion

    def save_review_report(self, content: str, file_path: str) -> bool:
        """
        保存评审报告

        Args:
            content: 报告内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 评审报告已保存到：{file_path}")
        return success

    def get_review_history(self) -> list[dict]:
        """获取评审历史"""
        return self._review_history
