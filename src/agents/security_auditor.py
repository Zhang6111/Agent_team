"""安全审计 Agent - 代码漏洞扫描、权限越界风险检测"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 安全审计 Agent 的系统提示词
SECURITY_AUDITOR_PROMPT = """你是安全审计专家，负责扫描代码漏洞和权限越界风险。

你的职责：
1. 扫描代码中的安全漏洞
2. 检测权限越界风险
3. 检查敏感信息泄露
4. 评估安全风险等级
5. 提供修复建议

审计维度：
- SQL 注入
- XSS 跨站脚本
- CSRF 跨站请求伪造
- 命令注入
- 路径遍历
- 敏感信息泄露（密码、Key、Token）
- 弱加密
- 权限校验缺失
- 输入验证缺失
- 日志泄露风险

输出格式：
```
# 安全审计报告

## 1. 审计概述
- 审计文件
- 审计时间
- 风险等级

## 2. 漏洞清单
### 2.1 高危漏洞
| 位置 | 漏洞类型 | 描述 | 修复建议 |
|------|----------|------|----------|

### 2.2 中危漏洞
...

### 2.3 低危漏洞
...

## 3. 权限检查
- 认证机制
- 授权机制
- 越界风险

## 4. 敏感信息检查
- 硬编码密码
- API Key 泄露
- Token 处理

## 5. 修复建议
- 优先级排序
- 修复方案
- 参考资源

## 6. 审计结论
- 是否通过
- 必须修复的问题
- 建议修复的问题
```

注意：
- 安全问题要详细说明危害
- 提供具体的修复代码示例
- 高危问题必须立即修复"""


class SecurityAuditorAgent(BaseAgent):
    """
    安全审计 Agent
    
    负责：
    - 代码漏洞扫描
    - 权限越界检测
    - 敏感信息检查
    """

    def __init__(self, name: str = "SecurityAuditor", model: Optional[str] = None):
        """
        初始化安全审计 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
        """
        super().__init__(
            name=name,
            role="Security Auditor",
            system_prompt=SECURITY_AUDITOR_PROMPT,
            model=model,
        )

        # 工具实例
        self.file_tools = FileTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)
        
        # 审计记录
        self._audit_history: list[dict] = []

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

    def audit_code(self, code_content: str, file_path: str = "") -> str:
        """
        审计代码安全

        Args:
            code_content: 代码内容
            file_path: 文件路径

        Returns:
            审计报告
        """
        prompt = f"""
请对以下代码进行安全审计：

【文件】{file_path if file_path else '未知'}

【代码内容】
{code_content}

请检查以下安全问题：
1. SQL 注入风险
2. XSS 跨站脚本
3. CSRF 跨站请求伪造
4. 命令注入
5. 路径遍历
6. 敏感信息泄露（密码、Key、Token）
7. 弱加密算法
8. 权限校验缺失
9. 输入验证缺失
10. 日志泄露风险

请输出详细的安全审计报告，包括：
- 问题位置和描述
- 风险等级（High/Medium/Low）
- 修复建议和代码示例
"""
        audit = self.invoke(prompt)
        self._audit_history.append({
            "file": file_path,
            "audit": audit,
        })
        return audit

    def audit_file(self, file_path: str) -> str:
        """
        审计文件

        Args:
            file_path: 文件路径

        Returns:
            审计报告
        """
        try:
            code = self.file_tools.read_file(file_path)
            return self.audit_code(code, file_path)
        except Exception as e:
            return f"审计失败：{e}"

    def scan_secrets(self, code_content: str) -> list[dict]:
        """
        扫描敏感信息

        Args:
            code_content: 代码内容

        Returns:
            敏感信息列表
        """
        prompt = f"""
请扫描以下代码中的敏感信息：

{code_content}

检查项：
1. 硬编码密码
2. API Key / Secret
3. Token / Session ID
4. 数据库连接字符串
5. 私钥/证书
6. 个人敏感信息

请列出所有发现的敏感信息及其位置。
"""
        response = self.invoke(prompt)
        return [{"secrets": response}]

    def check_sql_injection(self, code_content: str) -> list[dict]:
        """
        检查 SQL 注入风险

        Args:
            code_content: 代码内容

        Returns:
            风险列表
        """
        risks = []
        # 检查常见的 SQL 注入模式
        dangerous_patterns = [
            "execute(",
            "cursor.execute(",
            "query(",
            "raw(",
            "executeQuery(",
        ]
        lines = code_content.split('\n')
        for i, line in enumerate(lines, 1):
            if any(p in line for p in dangerous_patterns):
                if '+' in line or 'f"' in line or "f'" in line or '%s' in line:
                    risks.append({
                        "line": i,
                        "type": "SQL Injection",
                        "code": line.strip(),
                        "severity": "High",
                    })
        return risks

    def check_xss(self, code_content: str) -> list[dict]:
        """
        检查 XSS 风险

        Args:
            code_content: 代码内容

        Returns:
            风险列表
        """
        risks = []
        # 检查常见的 XSS 风险模式
        dangerous_patterns = [
            "innerHTML",
            "document.write",
            "eval(",
            "dangerouslySetInnerHTML",
        ]
        lines = code_content.split('\n')
        for i, line in enumerate(lines, 1):
            if any(p in line for p in dangerous_patterns):
                if 'sanitize' not in line.lower() and 'escape' not in line.lower():
                    risks.append({
                        "line": i,
                        "type": "XSS",
                        "code": line.strip(),
                        "severity": "High",
                    })
        return risks

    def get_risk_level(self, audit_report: str) -> str:
        """
        评估风险等级

        Args:
            audit_report: 审计报告

        Returns:
            风险等级
        """
        if "高危" in audit_report or "High" in audit_report:
            return "High"
        elif "中危" in audit_report or "Medium" in audit_report:
            return "Medium"
        return "Low"

    def save_audit_report(self, content: str, file_path: str) -> bool:
        """
        保存审计报告

        Args:
            content: 报告内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 审计报告已保存到：{file_path}")
        return success

    def get_audit_history(self) -> list[dict]:
        """获取审计历史"""
        return self._audit_history

    def generate_security_checklist(self) -> str:
        """
        生成安全检查清单

        Returns:
            检查清单
        """
        checklist = """# 安全检查清单

## 认证与授权
- [ ] 所有接口都有认证保护
- [ ] 使用强密码策略
- [ ] 实现账户锁定机制
- [ ] 使用 OAuth2/JWT 等标准协议

## 输入验证
- [ ] 所有用户输入都验证
- [ ] 使用白名单验证
- [ ] 限制输入长度
- [ ] 验证文件上传类型

## 输出编码
- [ ] HTML 输出进行转义
- [ ] 使用参数化查询
- [ ] 设置 Content-Type

## 会话管理
- [ ] 使用安全的 Session ID
- [ ] 实现会话超时
- [ ] 登出后销毁会话

## 敏感数据保护
- [ ] 密码加密存储
- [ ] 敏感数据加密传输
- [ ] 不在日志中记录敏感信息

## 错误处理
- [ ] 不暴露详细错误信息
- [ ] 使用统一的错误页面
- [ ] 记录安全日志

## 依赖安全
- [ ] 定期更新依赖
- [ ] 检查依赖漏洞
- [ ] 使用锁定文件
"""
        return checklist
