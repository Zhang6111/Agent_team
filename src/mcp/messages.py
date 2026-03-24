"""MCP 通信层 - Agent 间消息传递"""
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class MessageType(Enum):
    """消息类型"""
    TASK = "task"              # 任务分发
    RESPONSE = "response"      # 任务响应
    REQUEST = "request"        # 请求协助
    STATUS = "status"          # 状态更新
    ERROR = "error"            # 错误通知
    BROADCAST = "broadcast"    # 广播消息


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class Message(BaseModel):
    """MCP 消息模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    sender: str                # 发送者 Agent 名称
    receiver: Optional[str] = None  # 接收者，None 表示广播
    content: Any               # 消息内容
    timestamp: datetime = Field(default_factory=datetime.now)
    parent_id: Optional[str] = None  # 父消息 ID（用于任务链）
    metadata: dict = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class TaskPayload(BaseModel):
    """任务负载"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str           # 任务描述
    requirements: list[str] = Field(default_factory=list)  # 要求列表
    context: dict = Field(default_factory=dict)  # 上下文信息
    deadline: Optional[str] = None  # 截止时间


class ResponsePayload(BaseModel):
    """响应负载"""
    task_id: str               # 关联的任务 ID
    success: bool              # 是否成功
    result: Any = None         # 结果数据
    error_message: Optional[str] = None  # 错误信息
    attachments: list[str] = Field(default_factory=list)  # 附加文件列表
