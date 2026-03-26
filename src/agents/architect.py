"""架构师 Agent - 技术架构设计"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 架构师 Agent 的系统提示词
ARCHITECT_PROMPT = """你是资深架构师，负责设计项目整体技术架构。

你的职责：
1. 根据 PRD 设计技术架构方案
2. 定义项目目录结构和规范
3. 设计技术选型和接口标准
4. 输出架构设计文档
5. 指导研发团队实现架构

工作流程：
1. 接收任务：通过 MessageBus 接收项目总监派发的架构设计任务
2. 分析需求：理解项目规模和技术要求
3. 设计架构：输出架构设计文档
4. 返回结果：通过 MessageBus 发送完成通知

可用工具：
- read_file: 读取需求文档或现有代码
- write_file: 创建架构设计文档
- file_exists: 检查文件是否存在
- list_directory: 列出目录结构

输出格式（架构设计文档模板）：
```
# 架构设计文档

## 1. 架构概述
- 架构图（文字描述）
- 核心组件
- 数据流向

## 2. 技术选型
### 2.1 前端技术栈
- 框架：
- 状态管理：
- 构建工具：

### 2.2 后端技术栈
- 语言：
- 框架：
- 数据库：

### 2.3 基础设施
- 部署方式：
- CI/CD:
- 监控：

## 3. 项目结构
```
project/
├── src/
├── tests/
├── docs/
└── ...
```

## 4. 接口设计
### 4.1 API 规范
- RESTful 规范
- 认证方式
- 错误码定义

### 4.2 核心接口列表

## 5. 数据设计
### 5.1 数据模型
### 5.2 数据库表结构

## 6. 安全设计
- 认证授权
- 数据加密
- 防护措施

## 7. 性能设计
- 缓存策略
- 数据库优化
- 负载均衡
```

注意：
- 架构要可扩展、可维护
- 技术选型要合理、成熟
- 考虑安全性和性能"""


class ArchitectAgent(BaseAgent):
    """
    架构师 Agent
    
    负责：
    - 技术架构设计
    - 项目结构定义
    - 技术选型
    """

    def __init__(self, name: str = "Architect", model: Optional[str] = None, memory=None):
        """
        初始化架构师 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
            memory: 记忆模块
        """
        super().__init__(
            name=name,
            role="Software Architect",
            system_prompt=ARCHITECT_PROMPT,
            model=model,
            memory=memory,
        )

        # 工具实例
        self.file_tools = FileTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)
        
        # 缓存的架构设计
        self._architecture_cache: dict[str, str] = {}

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

    def design_architecture(self, prd_content: str) -> str:
        """
        根据 PRD 设计技术架构

        Args:
            prd_content: PRD 文档内容

        Returns:
            架构设计文档
        """
        prompt = f"""
请根据以下 PRD 设计技术架构：

【PRD 内容】
{prd_content}

请输出完整的架构设计文档，包括：
1. 技术选型（前端/后端/数据库）
2. 项目目录结构
3. 核心模块设计
4. API 接口规范
5. 数据库设计（如需要）
"""
        architecture = self.invoke(prompt)
        return architecture

    def save_architecture(self, content: str, file_path: str) -> bool:
        """
        保存架构设计到文件

        Args:
            content: 架构设计内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, content)
        if success:
            print(f"✓ 架构设计已保存到：{file_path}")
        return success

    def create_project_structure(self, base_path: str, structure: dict) -> bool:
        """
        创建项目目录结构

        Args:
            base_path: 基础路径
            structure: 目录结构定义

        Returns:
            是否创建成功
        """
        try:
            def create_recursive(path: str, struct: dict):
                for name, content in struct.items():
                    full_path = f"{path}/{name}"
                    if isinstance(content, dict):
                        # 是目录
                        self.file_tools.create_directory(full_path)
                        create_recursive(full_path, content)
                    elif content is None:
                        # 是空文件
                        self.file_tools.write_file(full_path, "")
                    else:
                        # 是文件，写入内容
                        self.file_tools.write_file(full_path, content)
            
            self.file_tools.create_directory(base_path)
            create_recursive(base_path, structure)
            return True
        except Exception as e:
            print(f"创建项目结构失败：{e}")
            return False

    def generate_api_template(self, api_name: str, methods: list[str]) -> str:
        """
        生成 API 模板代码

        Args:
            api_name: API 名称
            methods: HTTP 方法列表

        Returns:
            API 模板代码
        """
        template = f"""
# {api_name} API

## 接口列表

"""
        for method in methods:
            template += f"""
### {method.upper()} /api/{api_name}

**请求参数:**

**响应格式:**

**错误码:**

"""
        return template
