"""MCP 消息总线 - Agent 通信中枢"""
import asyncio
from typing import Callable, Optional
from collections import defaultdict
from src.mcp.messages import Message, MessageType, MessagePriority


class MessageBus:
    """消息总线 - 管理所有 Agent 间的通信"""

    def __init__(self):
        # 订阅者注册表：agent_name -> [callback functions]
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        # 消息队列
        self._queue: asyncio.Queue = asyncio.Queue()
        # 运行状态
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def subscribe(self, agent_name: str, callback: Callable[[Message], None]) -> None:
        """
        订阅消息

        Args:
            agent_name: Agent 名称
            callback: 消息回调函数
        """
        self._subscribers[agent_name].append(callback)

    def unsubscribe(self, agent_name: str, callback: Callable) -> None:
        """取消订阅"""
        if agent_name in self._subscribers:
            self._subscribers[agent_name].remove(callback)

    async def publish(self, message: Message) -> None:
        """
        发布消息

        Args:
            message: 要发布的消息
        """
        await self._queue.put(message)

    def publish_sync(self, message: Message) -> None:
        """同步发布消息（用于非异步上下文）"""
        asyncio.create_task(self.publish(message))

    async def _process_message(self, message: Message) -> None:
        """处理单条消息，分发给订阅者"""
        # 广播消息：发送给所有订阅者
        if message.receiver is None:
            for agent_name, callbacks in self._subscribers.items():
                for callback in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(message)
                        else:
                            callback(message)
                    except Exception as e:
                        print(f"[MCP] 发送消息给 {agent_name} 失败：{e}")
        # 点对点消息：只发送给指定接收者
        elif message.receiver in self._subscribers:
            for callback in self._subscribers[message.receiver]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    print(f"[MCP] 发送消息给 {message.receiver} 失败：{e}")

    async def run(self) -> None:
        """运行消息总线（持续处理队列）"""
        self._running = True
        while self._running:
            try:
                message = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._process_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[MCP] 处理消息失败：{e}")

    def stop(self) -> None:
        """停止消息总线"""
        self._running = False

    async def start_async(self) -> None:
        """异步启动消息总线"""
        self._task = asyncio.create_task(self.run())

    def get_subscribers(self, agent_name: str) -> list:
        """获取指定 Agent 的所有订阅回调"""
        return self._subscribers.get(agent_name, [])

    @property
    def subscriber_count(self) -> int:
        """获取订阅者数量"""
        return len(self._subscribers)


# 全局消息总线实例
message_bus = MessageBus()
