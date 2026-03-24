"""技术文档 Agent - 自动生成接口/部署/维护全套文档"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 技术文档 Agent 的系统提示词
TECHNICAL_WRITER_PROMPT = """你是技术文档工程师，负责自动生成接口/部署/维护全套文档。

你的职责：
1. 编写 API 接口文档
2. 编写部署文档
3. 编写用户手册
4. 编写维护文档
5. 确保文档完整、准确、易懂

文档类型：
- API 文档（OpenAPI/Swagger）
- 部署文档（Deployment Guide）
- 用户手册（User Manual）
- 开发文档（Developer Guide）
- 维护文档（Maintenance Guide）
- 架构文档（Architecture Document）
- README 文档

输出格式（API 文档模板）：
```
# API 文档

## 1. 概述
- API 版本
- 基础 URL
- 认证方式

## 2. 快速开始
- 认证说明
- 请求格式
- 响应格式

## 3. 接口列表
### 3.1 接口名称
**请求**
- 方法：GET/POST/PUT/DELETE
- 路径：/api/xxx
- 认证：需要/不需要

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|

**响应示例**
```json
{}
```

**错误码**
| 码 | 说明 |
|----|------|
```

注意：
- 文档要清晰、完整
- 包含使用示例
- 考虑读者技术水平"""


class TechnicalWriterAgent(BaseAgent):
    """
    技术文档 Agent
    
    负责：
    - API 文档生成
    - 部署文档编写
    - 用户手册编写
    """

    def __init__(self, name: str = "TechnicalWriter", model: Optional[str] = None, memory=None):
        """
        初始化技术文档 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
            memory: 记忆模块
        """
        super().__init__(
            name=name,
            role="Technical Writer",
            system_prompt=TECHNICAL_WRITER_PROMPT,
            model=model,
            memory=memory,
        )

        # 工具实例
        self.file_tools = FileTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)
        
        # 文档记录
        self._document_history: list[dict] = []

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

    def generate_api_doc(self, code_content: str, prd_content: str = "") -> str:
        """
        生成 API 文档

        Args:
            code_content: 代码内容
            prd_content: PRD 内容

        Returns:
            API 文档
        """
        prompt = f"""
请根据以下代码生成 API 文档：

【代码内容】
{code_content}

【PRD 内容】
{prd_content if prd_content else '无'}

请生成完整的 API 文档，包括：
1. API 概述（版本、基础 URL、认证方式）
2. 快速开始指南
3. 所有接口列表（方法、路径、参数、响应）
4. 请求/响应示例
5. 错误码说明
6. 速率限制（如有）
"""
        doc = self.invoke(prompt)
        self._document_history.append({
            "type": "API",
            "content": doc,
        })
        return doc

    def generate_deployment_doc(self, architecture: str, tech_stack: dict) -> str:
        """
        生成部署文档

        Args:
            architecture: 架构描述
            tech_stack: 技术栈

        Returns:
            部署文档
        """
        prompt = f"""
请生成部署文档：

【架构描述】
{architecture}

【技术栈】
{tech_stack}

请生成完整的部署文档，包括：
1. 环境要求（操作系统、运行时、依赖服务）
2. 部署准备（账号、权限、网络）
3. 部署步骤（安装、配置、启动）
4. 验证部署（健康检查、测试）
5. 常见问题排查
6. 回滚方案
"""
        doc = self.invoke(prompt)
        self._document_history.append({
            "type": "Deployment",
            "content": doc,
        })
        return doc

    def generate_readme(self, project_info: dict) -> str:
        """
        生成 README

        Args:
            project_info: 项目信息

        Returns:
            README 内容
        """
        prompt = f"""
请为以下项目生成 README 文档：

【项目信息】
{project_info}

请生成完整的 README，包括：
1. 项目简介
2. 功能特性
3. 技术栈
4. 快速开始（安装、配置、运行）
5. 使用示例
6. 项目结构
7. 贡献指南
8. License
"""
        readme = self.invoke(prompt)
        self._document_history.append({
            "type": "README",
            "content": readme,
        })
        return readme

    def generate_user_manual(self, features: list[str]) -> str:
        """
        生成用户手册

        Args:
            features: 功能列表

        Returns:
            用户手册
        """
        prompt = f"""
请生成用户手册：

【功能列表】
{features}

请生成完整的用户手册，包括：
1. 产品简介
2. 快速入门
3. 功能详解（每个功能的使用说明）
4. 常见问题
5. 技术支持
"""
        manual = self.invoke(prompt)
        self._document_history.append({
            "type": "UserManual",
            "content": manual,
        })
        return manual

    def generate_architecture_doc(self, design_doc: str) -> str:
        """
        生成架构文档

        Args:
            design_doc: 设计文档

        Returns:
            架构文档
        """
        prompt = f"""
请根据以下设计文档生成架构文档：

【设计文档】
{design_doc}

请生成完整的架构文档，包括：
1. 架构概述
2. 核心组件
3. 数据流
4. 技术选型说明
5. 扩展性设计
6. 安全性设计
"""
        doc = self.invoke(prompt)
        self._document_history.append({
            "type": "Architecture",
            "content": doc,
        })
        return doc

    def generate_maintenance_doc(self, system_info: dict) -> str:
        """
        生成维护文档

        Args:
            system_info: 系统信息

        Returns:
            维护文档
        """
        prompt = f"""
请生成维护文档：

【系统信息】
{system_info}

请生成完整的维护文档，包括：
1. 系统概述
2. 日常维护任务（巡检、备份、监控）
3. 故障排查指南
4. 日志说明
5. 性能调优建议
6. 升级指南
"""
        doc = self.invoke(prompt)
        self._document_history.append({
            "type": "Maintenance",
            "content": doc,
        })
        return doc

    def save_document(self, content: str, file_path: str) -> bool:
        """
        保存文档

        Args:
            content: 文档内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 文档已保存到：{file_path}")
        return success

    def get_document_history(self) -> list[dict]:
        """获取文档历史"""
        return self._document_history

    def generate_openapi_spec(self, api_doc: str) -> str:
        """
        生成 OpenAPI 规范

        Args:
            api_doc: API 文档

        Returns:
            OpenAPI YAML/JSON
        """
        prompt = f"""
请根据以下 API 文档生成 OpenAPI 3.0 规范：

{api_doc}

请生成标准的 OpenAPI 3.0 YAML 格式，包括：
- info（标题、版本、描述）
- servers
- paths（所有接口）
- components（schemas）
- security
"""
        spec = self.invoke(prompt)
        return spec
