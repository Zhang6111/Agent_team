"""记忆系统 - 管理对话历史和任务上下文"""
import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class TaskContext(BaseModel):
    """任务上下文"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class SessionMemory:
    """
    会话记忆系统
    
    管理：
    1. 对话历史（短期记忆）
    2. 任务上下文（共享状态）
    3. 文件操作记录
    """

    def __init__(self, max_turns: int = 50):
        """
        初始化会话记忆

        Args:
            max_turns: 最大保留对话轮数
        """
        # 对话历史记忆
        self.chat_history = ChatMessageHistory()
        self.max_turns = max_turns
        
        # 当前任务上下文
        self.current_task: Optional[TaskContext] = None
        
        # 任务历史
        self.task_history: list[TaskContext] = []
        
        # 文件操作记录
        self.created_files: list[str] = []
        self.modified_files: list[str] = []
        
        # 项目状态
        self.project_info: dict = {
            "name": "",
            "description": "",
            "tech_stack": [],
        }
        
        # 原始对话记录（用于调试）
        self.raw_history: list[dict] = []

    def add_user_message(self, message: str) -> None:
        """添加用户消息"""
        self.chat_history.add_user_message(message)
        self.raw_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
        })

    def add_ai_message(self, message: str) -> None:
        """添加 AI 消息"""
        self.chat_history.add_ai_message(message)
        self.raw_history.append({
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat(),
        })

    def get_history(self) -> list:
        """获取对话历史"""
        return self.chat_history.messages

    def get_history_string(self) -> str:
        """获取格式化的历史字符串"""
        messages = self.chat_history.messages
        history_str = ""
        for msg in messages[-20:]:  # 最近 20 条
            if isinstance(msg, HumanMessage):
                history_str += f"用户：{msg.content}\n"
            elif isinstance(msg, AIMessage):
                history_str += f"助手：{msg.content}\n"
        return history_str

    def clear_history(self) -> None:
        """清空历史"""
        self.chat_history.clear()
        self.raw_history.clear()

    def start_task(self, description: str) -> TaskContext:
        """开始新任务"""
        task = TaskContext(description=description)
        self.current_task = task
        return task

    def complete_task(self, result: str) -> None:
        """完成任务"""
        if self.current_task:
            self.current_task.status = "completed"
            self.current_task.result = result
            self.task_history.append(self.current_task)
            self.current_task = None

    def fail_task(self, error: str) -> None:
        """任务失败"""
        if self.current_task:
            self.current_task.status = "failed"
            self.current_task.result = error
            self.task_history.append(self.current_task)
            self.current_task = None

    def add_file(self, file_path: str, is_modification: bool = False) -> None:
        """记录文件操作"""
        if is_modification:
            if file_path not in self.modified_files:
                self.modified_files.append(file_path)
        else:
            if file_path not in self.created_files:
                self.created_files.append(file_path)

    def get_context_summary(self) -> str:
        """获取上下文摘要"""
        summary = []
        
        if self.current_task:
            summary.append(f"当前任务：{self.current_task.description}")
        
        if self.created_files:
            summary.append(f"已创建文件：{', '.join(self.created_files[-5:])}")
        
        if self.modified_files:
            summary.append(f"已修改文件：{', '.join(self.modified_files[-5:])}")
        
        return "\n".join(summary) if summary else "无上下文信息"

    def to_context_prompt(self) -> str:
        """生成上下文提示词"""
        context = []
        
        # 对话历史
        history = self.get_history_string()
        if history:
            context.append(f"【对话历史】\n{history}")
        
        # 当前任务
        if self.current_task:
            context.append(f"【当前任务】\n{self.current_task.description}")
        
        # 文件记录
        if self.created_files:
            context.append(f"【已创建文件】\n{', '.join(self.created_files)}")
        
        # 项目信息
        if self.project_info["name"]:
            context.append(
                f"【项目信息】\n"
                f"名称：{self.project_info['name']}\n"
                f"描述：{self.project_info['description']}\n"
                f"技术栈：{', '.join(self.project_info['tech_stack'])}"
            )
        
        return "\n\n".join(context)

    def get_recent_tasks(self, limit: int = 5) -> list[TaskContext]:
        """获取最近的任务"""
        return self.task_history[-limit:]


# 全局会话记忆实例
session_memory = SessionMemory()
