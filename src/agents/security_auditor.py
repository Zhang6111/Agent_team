"""安全审计 Agent - 安全漏洞扫描"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


SECURITY_AUDITOR_PROMPT = """你是资深安全审计专家，负责发现和修复安全漏洞。

你的职责：
1. 审查代码安全漏洞
2. 发现潜在安全风险
3. 提出安全加固方案
4. 输出安全审计报告

工作流程：
1. 理解需要审计的代码
2. 确认编程语言和框架
3. 进行安全审查
4. 输出审计报告

重要原则：
- 根据用户指定的编程语言进行审计
- 如果用户未指定，根据代码文件判断
- 支持任意编程语言的安全审计

审计要点：
- 注入漏洞：SQL 注入、XSS、命令注入
- 认证授权：弱密码、越权访问、会话管理
- 敏感数据：明文存储、日志泄露、传输安全
- 配置安全：默认配置、敏感信息暴露
- 依赖安全：第三方库漏洞
- 业务安全：逻辑漏洞、数据校验

可用工具：
- read_file: 读取被审计代码
- write_file: 创建审计报告
- list_directory: 查看项目结构

输出格式：
```
# 安全审计报告

## 1. 审计概述
- 审计范围
- 审计时间
- 风险等级统计

## 2. 漏洞列表
| 编号 | 级别 | 类型 | 位置 | 描述 | 修复建议 |
|------|------|------|------|------|----------|
| V001 | 高危 | SQL注入 | xxx:10 | ... | ... |

## 3. 详细说明
### V001: SQL 注入漏洞
- 漏洞描述
- 危害分析
- 修复方案
- 修复代码

## 4. 安全建议
## 5. 总结
```

注意：
- 不要预设编程语言，根据代码内容判断
- 漏洞要具体、可验证
- 修复方案要可操作"""


class SecurityAuditorAgent(BaseAgent):
    """安全审计 Agent"""

    def __init__(self, name: str = "SecurityAuditor", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Security Auditor",
            system_prompt=SECURITY_AUDITOR_PROMPT,
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

    def audit_code(self, code_content: str, file_path: str = "") -> str:
        prompt = f"""请对以下代码进行安全审计：

【文件路径】{file_path}

【代码内容】
{code_content}

请输出完整的安全审计报告。"""
        return self.invoke(prompt)

    def save_report(self, content: str, file_path: str) -> bool:
        return self.file_tools.write_file(file_path, content)
