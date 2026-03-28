"""性能优化 Agent - 性能分析与优化"""
from typing import Optional
from src.agents.base_agent import BaseAgent
from src.tools.file_tools import get_file_tools
from src.mcp import message_bus, Message, MessageType, TaskPayload, ResponsePayload


PERFORMANCE_OPTIMIZER_PROMPT = """你是资深性能优化专家，负责分析和优化系统性能。

你的职责：
1. 分析性能瓶颈
2. 优化代码性能
3. 优化数据库查询
4. 提出架构优化方案

工作流程：
1. 理解性能问题
2. 确认技术栈
3. 使用 read_file 读取代码
4. 使用 write_file 保存优化报告

重要原则：
- 根据用户指定的技术栈进行优化
- 如果用户未指定，主动询问或使用 read_file 读取项目文件判断
- 支持任意编程语言和框架的性能优化

优化方向：
- 算法优化：时间复杂度、空间复杂度
- 数据库优化：索引、查询、分库分表
- 缓存优化：Redis、本地缓存
- 并发优化：多线程、异步、协程
- 网络优化：CDN、压缩、连接池
- 内存优化：泄漏检测、对象池

可用工具：
- read_file(file_path): 读取代码
- write_file(file_path, content): 创建优化报告
- list_directory(dir_path): 查看项目结构

重要：优化报告使用 write_file 工具写入文件！

注意：
- 不要预设技术栈，根据用户需求判断
- 优化要有数据支撑
- 方案要可落地"""


class PerformanceOptimizerAgent(BaseAgent):
    """性能优化 Agent"""

    def __init__(self, name: str = "PerformanceOptimizer", model: Optional[str] = None, memory=None):
        super().__init__(
            name=name,
            role="Performance Optimizer",
            system_prompt=PERFORMANCE_OPTIMIZER_PROMPT,
            model=model,
            memory=memory,
            tools=get_file_tools(),
        )

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
