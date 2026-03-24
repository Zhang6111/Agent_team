"""故障修复 Agent - Bug 修复、问题闭环"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools, CommandTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 故障修复 Agent 的系统提示词
BUG_FIXER_PROMPT = """你是故障修复专家，负责修复测试发现的 Bug 和问题。

你的职责：
1. 分析 Bug 报告和问题描述
2. 定位问题根源
3. 提供修复方案
4. 实施代码修复
5. 验证修复效果
6. 确保问题闭环

工作流程：
1. 接收 Bug 报告/错误日志
2. 分析问题原因
3. 制定修复方案
4. 修改代码
5. 运行测试验证
6. 输出修复报告

输出格式：
```
# Bug 修复报告

## 1. Bug 信息
- Bug ID
- 严重程度
- 影响范围

## 2. 问题分析
- 问题现象
- 根本原因
- 影响模块

## 3. 修复方案
- 修复思路
- 修改内容
- 风险评估

## 4. 代码修改
```diff
- 原代码
+ 新代码
```

## 5. 验证结果
- 测试用例
- 验证步骤
- 通过情况

## 6. 后续建议
- 如何避免类似问题
- 需要改进的地方
```

注意：
- 修复前要备份原代码
- 修改要最小化，避免引入新问题
- 修复后必须验证"""


class BugFixerAgent(BaseAgent):
    """
    故障修复 Agent
    
    负责：
    - Bug 分析
    - 代码修复
    - 问题闭环
    """

    def __init__(self, name: str = "BugFixer", model: Optional[str] = None):
        """
        初始化故障修复 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
        """
        super().__init__(
            name=name,
            role="Bug Fixer",
            system_prompt=BUG_FIXER_PROMPT,
            model=model,
        )

        # 工具实例
        self.file_tools = FileTools()
        self.command_tools = CommandTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)
        
        # 修复记录
        self._fix_history: list[dict] = []

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

    def analyze_bug(self, bug_report: str, code_content: str = "") -> str:
        """
        分析 Bug

        Args:
            bug_report: Bug 报告
            code_content: 相关代码

        Returns:
            分析报告
        """
        prompt = f"""
请分析以下 Bug：

【Bug 报告】
{bug_report}

【相关代码】
{code_content if code_content else '无'}

请分析：
1. 问题现象
2. 可能的根本原因
3. 影响范围
4. 复现步骤
5. 修复优先级
"""
        analysis = self.invoke(prompt)
        return analysis

    def fix_bug(self, bug_report: str, code_content: str) -> tuple[str, str]:
        """
        修复 Bug

        Args:
            bug_report: Bug 报告
            code_content: 代码内容

        Returns:
            (修复后的代码，修复说明)
        """
        prompt = f"""
请修复以下 Bug：

【Bug 报告】
{bug_report}

【代码内容】
{code_content}

请：
1. 说明修复方案
2. 提供修复后的完整代码
3. 说明修改了哪些地方
4. 提供验证方法

请以以下格式返回：
【修复说明】
...

【修复后的代码】
...
"""
        response = self.invoke(prompt)
        
        # 解析响应
        if "【修复后的代码】" in response:
            parts = response.split("【修复后的代码】")
            explanation = parts[0].replace("【修复说明】", "").strip()
            fixed_code = parts[1].strip()
        else:
            explanation = "修复完成"
            fixed_code = response
        
        self._fix_history.append({
            "bug_report": bug_report,
            "explanation": explanation,
        })
        
        return fixed_code, explanation

    def apply_fix(self, file_path: str, fixed_code: str) -> bool:
        """
        应用修复

        Args:
            file_path: 文件路径
            fixed_code: 修复后的代码

        Returns:
            是否成功
        """
        # 备份原文件
        backup_path = file_path + ".bak"
        try:
            original = self.file_tools.read_file(file_path)
            self.file_tools.write_file(backup_path, original)
            print(f"✓ 已备份原文件：{backup_path}")
        except Exception as e:
            print(f"备份失败：{e}")
        
        # 应用修复
        return self.file_tools.write_file(file_path, fixed_code)

    def generate_diff(self, original: str, fixed: str) -> str:
        """
        生成差异对比

        Args:
            original: 原代码
            fixed: 修复后的代码

        Returns:
            Diff 字符串
        """
        original_lines = original.splitlines(keepends=True)
        fixed_lines = fixed.splitlines(keepends=True)
        
        diff = []
        diff.append("--- original\n")
        diff.append("+++ fixed\n")
        
        # 简单 diff
        for i, (o, f) in enumerate(zip(original_lines, fixed_lines)):
            if o != f:
                diff.append(f"@@ -{i+1} +{i+1} @@\n")
                diff.append(f"-{o}")
                diff.append(f"+{f}")
        
        return "".join(diff)

    def verify_fix(
        self, test_command: str, cwd: Optional[str] = None
    ) -> tuple[int, str]:
        """
        验证修复

        Args:
            test_command: 测试命令
            cwd: 工作目录

        Returns:
            (返回码，输出)
        """
        return self.command_tools.run_command_stream(test_command, cwd=cwd)

    def save_fix_report(self, content: str, file_path: str) -> bool:
        """
        保存修复报告

        Args:
            content: 报告内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 修复报告已保存到：{file_path}")
        return success

    def get_fix_history(self) -> list[dict]:
        """获取修复历史"""
        return self._fix_history
