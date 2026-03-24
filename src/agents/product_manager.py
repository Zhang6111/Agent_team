"""产品 Agent - 需求分析与 PRD 输出"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


# 产品 Agent 的系统提示词
PRODUCT_MANAGER_PROMPT = """你是产品经理，负责需求分析和功能规划。

你的职责：
1. 理解用户/项目总监提出的需求
2. 分析需求并输出标准化 PRD（产品需求文档）
3. 拆解功能点和用户故事
4. 定义优先级和验收标准
5. 协助研发团队理解需求

输出格式（PRD 模板）：
```
# 产品需求文档

## 1. 项目概述
- 项目背景
- 目标用户
- 核心价值

## 2. 功能需求
### 2.1 功能列表
- [P0] 高优先级功能
- [P1] 中优先级功能
- [P2] 低优先级功能

### 2.2 功能详情
#### 功能名称
- 描述
- 用户故事
- 验收标准

## 3. 非功能需求
- 性能要求
- 安全要求
- 兼容性要求

## 4. 数据需求
- 核心数据模型
- 数据存储要求

## 5. 接口需求
- 外部接口
- 内部 API

## 6. 其他说明
```

注意：
- 需求要清晰、可执行
- 优先级要明确
- 验收标准要可量化"""


class ProductManagerAgent(BaseAgent):
    """
    产品 Agent
    
    负责：
    - 需求分析
    - 输出 PRD 文档
    - 功能拆解
    """

    def __init__(self, name: str = "ProductManager", model: Optional[str] = None):
        """
        初始化产品 Agent

        Args:
            name: Agent 名称
            model: 使用的模型名称
        """
        super().__init__(
            name=name,
            role="Product Manager",
            system_prompt=PRODUCT_MANAGER_PROMPT,
            model=model,
        )

        # 工具实例
        self.file_tools = FileTools()
        
        # 订阅 MCP 消息
        message_bus.subscribe(self.name, self._handle_message)
        
        # 缓存的 PRD
        self._prd_cache: dict[str, str] = {}

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

    def analyze_requirement(self, requirement: str) -> str:
        """
        分析需求并生成 PRD

        Args:
            requirement: 需求描述

        Returns:
            PRD 文档内容
        """
        prompt = f"""
请分析以下需求并生成标准化的 PRD 文档：

【需求描述】
{requirement}

请按照 PRD 模板输出完整文档。
"""
        prd = self.invoke(prompt)
        return prd

    def save_prd(self, prd_content: str, file_path: str) -> bool:
        """
        保存 PRD 到文件

        Args:
            prd_content: PRD 内容
            file_path: 文件路径

        Returns:
            是否保存成功
        """
        success = self.file_tools.write_file(file_path, prd_content)
        if success:
            print(f"✓ PRD 已保存到：{file_path}")
        return success

    def extract_features(self, prd_content: str) -> list[dict]:
        """
        从 PRD 中提取功能列表

        Args:
            prd_content: PRD 内容

        Returns:
            功能列表
        """
        # 简单解析，实际可以用更复杂的 NLP 处理
        features = []
        lines = prd_content.split('\n')
        for line in lines:
            if '[P0]' in line or '[P1]' in line or '[P2]' in line:
                features.append({
                    'priority': 'P0' if '[P0]' in line else ('P1' if '[P1]' in line else 'P2'),
                    'description': line.split(']')[-1].strip()
                })
        return features

    def get_user_stories(self, prd_content: str) -> list[str]:
        """
        从 PRD 中提取用户故事

        Args:
            prd_content: PRD 内容

        Returns:
            用户故事列表
        """
        stories = []
        # 简单提取包含"用户故事"的行
        lines = prd_content.split('\n')
        for i, line in enumerate(lines):
            if '用户故事' in line or '作为' in line:
                stories.append(line.strip())
        return stories
