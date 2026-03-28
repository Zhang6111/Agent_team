"""产品 Agent - 需求分析与 PRD 输出"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools import FileTools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


PRODUCT_MANAGER_PROMPT = """你是产品经理，负责需求分析和功能规划。

你的职责：
1. 理解用户提出的需求
2. 分析需求并输出标准化 PRD（产品需求文档）
3. 拆解功能点和用户故事
4. 定义优先级和验收标准
5. 协助研发团队理解需求

工作流程：
1. 理解需求背景和目标
2. 分析功能需求和非功能需求
3. 输出 PRD 文档
4. 跟进需求实现

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

## 4. 其他说明
```

可用工具：
- read_file: 读取现有文档
- write_file: 创建/保存 PRD 文档
- file_exists: 检查文件是否存在

注意：
- 需求要清晰、可执行
- 优先级要明确
- 验收标准要可量化
- 不预设技术栈，技术选型由架构师决定"""


class ProductManagerAgent(BaseAgent):
    """产品 Agent - 负责需求分析和 PRD 输出"""

    def __init__(self, name: str = "ProductManager", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Product Manager",
            system_prompt=PRODUCT_MANAGER_PROMPT,
            model=model,
            memory=memory,
        )

        self.file_tools = FileTools()
        message_bus.subscribe(self.name, self._handle_message)
        self._prd_cache: dict[str, str] = {}

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

    def analyze_requirement(self, requirement: str) -> str:
        prd = self.invoke(f"请分析以下需求并生成 PRD 文档：\n\n{requirement}")
        return prd

    def save_prd(self, prd_content: str, file_path: str) -> bool:
        success = self.file_tools.write_file(file_path, prd_content)
        if success:
            print(f"✓ PRD 已保存到：{file_path}")
        return success

    def extract_features(self, prd_content: str) -> list[dict]:
        features = []
        lines = prd_content.split('\n')
        for line in lines:
            if '[P0]' in line or '[P1]' in line or '[P2]' in line:
                features.append({
                    'priority': 'P0' if '[P0]' in line else ('P1' if '[P1]' in line else 'P2'),
                    'description': line.split(']')[-1].strip()
                })
        return features
