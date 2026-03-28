"""产品 Agent - 智能产品助手（增强版）"""
from typing import Optional, List, Dict
from src.agents.base_agent import BaseAgent
from src.tools.file_tools import get_file_tools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


PRODUCT_MANAGER_PROMPT = """你是资深产品经理，负责需求分析、产品规划和决策支持。

你的职责：
1. 需求调研与分析
   - 理解用户需求，挖掘隐性需求
   - 生成用户故事和用户画像
   - 竞品分析和市场调研

2. 产品文档输出
   - 输出标准化 PRD 文档
   - 生成流程图（Mermaid 格式）
   - 生成页面原型描述

3. 决策支持
   - 功能优先级排序
   - 工作量估算
   - 风险评估

4. 变更管理
   - 版本对比
   - 变更影响分析
   - 变更日志生成

工作流程：
1. 理解需求背景和目标
2. 分析功能需求和非功能需求
3. 生成用户故事和验收标准
4. 使用 write_file 工具将 PRD 文档保存到 docs/PRD.md
5. 使用 write_file 工具将流程图保存到 docs/flowchart.md
6. 进行优先级排序和工作量估算

重要：所有文档必须使用 write_file 工具写入文件，不要直接输出内容！

可用工具：
- write_file(file_path, content): 创建文件，file_path 为文件路径，content 为文件内容
- read_file(file_path): 读取文件内容
- list_directory(dir_path): 列出目录内容
- create_directory(dir_path): 创建目录

输出规范：
- 需求要清晰、可执行
- 优先级要有依据
- 验收标准要可量化
- 流程图使用 Mermaid 格式
- 不预设技术栈，技术选型由架构师决定"""


class ProductManagerAgent(BaseAgent):
    """产品 Agent - 智能产品助手"""

    def __init__(self, name: str = "ProductManager", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Product Manager",
            system_prompt=PRODUCT_MANAGER_PROMPT,
            model=model,
            memory=memory,
            tools=get_file_tools(),
        )

        message_bus.subscribe(self.name, self._handle_message)
        self._prd_cache: Dict[str, str] = {}

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

    def extract_features(self, prd_content: str) -> List[Dict]:
        """从 PRD 中提取功能列表"""
        features = []
        lines = prd_content.split('\n')
        for line in lines:
            if '[P0]' in line or '[P1]' in line or '[P2]' in line:
                features.append({
                    'priority': 'P0' if '[P0]' in line else ('P1' if '[P1]' in line else 'P2'),
                    'description': line.split(']')[-1].strip()
                })
        return features
