"""FastAPI Server - 为 Node.js CLI 提供 API"""
import asyncio
import json
from typing import Optional, List
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 导入 Agent 系统
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.memory import session_memory
from src.agents import ProjectDirector


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    actions: List[dict] = []
    session_id: str


class AgentStatus(BaseModel):
    """Agent 状态"""
    name: str
    role: str
    status: str  # idle, working, done
    current_task: Optional[str] = None


class TeamStatus(BaseModel):
    """团队状态"""
    agents: List[AgentStatus]
    current_task: Optional[str] = None
    progress: int = 0


# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="Multi-Agent Team API",
    description="多 Agent 开发团队后端 API",
    version="1.0.0",
)

# CORS 配置（允许 Node.js CLI 连接）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
director: Optional[ProjectDirector] = None
websocket_clients: List[WebSocket] = []
agent_states: dict[str, dict] = {}
current_task: Optional[str] = None


# ==================== 辅助函数 ====================

def init_agent_team():
    """初始化 Agent 团队"""
    global director
    
    if director is None:
        director = ProjectDirector(memory=session_memory)
        
        # 初始化团队成员（简化版，实际应该和 main.py 一样）
        from src.agents import (
            TechLeadAgent, FrontendDeveloperAgent, BackendDeveloperAgent,
            ProductManagerAgent, ArchitectAgent, TesterAgent, DevOpsAgent,
            UIDesignerAgent, DataEngineerAgent, CodeReviewerAgent,
            BugFixerAgent, SecurityAuditorAgent, PerformanceOptimizerAgent,
            TechnicalWriterAgent,
        )
        
        # 添加团队成员并初始化状态
        team_members = [
            ("ProductManager", ProductManagerAgent),
            ("UIDesigner", UIDesignerAgent),
            ("Architect", ArchitectAgent),
            ("DataEngineer", DataEngineerAgent),
            ("TechLead", TechLeadAgent),
            ("FrontendDev", lambda: FrontendDeveloperAgent(name="FrontendDev")),
            ("BackendDev", lambda: BackendDeveloperAgent(name="BackendDev")),
            ("CodeReviewer", CodeReviewerAgent),
            ("Tester", TesterAgent),
            ("BugFixer", BugFixerAgent),
            ("SecurityAuditor", SecurityAuditorAgent),
            ("PerformanceOptimizer", PerformanceOptimizerAgent),
            ("DevOps", DevOpsAgent),
            ("TechnicalWriter", TechnicalWriterAgent),
        ]
        
        for name, agent_cls in team_members:
            agent = agent_cls(memory=session_memory)
            director.add_team_member(name, agent)
            agent_states[name] = {
                "name": name,
                "role": agent.role,
                "status": "idle",
                "current_task": None,
            }
    
    return director


async def broadcast_status():
    """广播状态给所有 WebSocket 客户端"""
    if not websocket_clients:
        return
    
    status = {
        "type": "status_update",
        "agents": list(agent_states.values()),
        "current_task": current_task,
        "timestamp": datetime.now().isoformat(),
    }
    
    disconnected = []
    for client in websocket_clients:
        try:
            await client.send_json(status)
        except:
            disconnected.append(client)
    
    # 移除断开的连接
    for client in disconnected:
        websocket_clients.remove(client)


def update_agent_status(name: str, status: str, task: Optional[str] = None):
    """更新 Agent 状态"""
    if name in agent_states:
        agent_states[name]["status"] = status
        if task:
            agent_states[name]["current_task"] = task
        asyncio.create_task(broadcast_status())


# ==================== API 路由 ====================

@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    init_agent_team()
    print("🚀 Multi-Agent Team API 已启动")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Multi-Agent Team API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/team")
async def get_team_status():
    """获取团队状态"""
    return {
        "agents": list(agent_states.values()),
        "current_task": current_task,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口
    
    接收用户消息，返回 Agent 响应和操作指令
    """
    global current_task
    
    if director is None:
        raise HTTPException(status_code=500, detail="Agent 团队未初始化")
    
    # 更新任务
    current_task = request.message
    update_agent_status("ProjectDirector", "working", request.message)
    
    try:
        # 调用项目总监
        response = director.invoke(request.message)
        
        # 解析响应中的操作指令
        actions = []
        executor = None  # 这里可以添加 CLIExecutor 来解析
        
        # 更新记忆
        session_memory.add_user_message(request.message)
        session_memory.add_ai_message(response)
        
        # 如果没有开始任务，启动一个
        if not session_memory.current_task:
            session_memory.start_task(request.message)
        
        return ChatResponse(
            message=response,
            actions=actions,
            session_id=session_memory.current_task.task_id if session_memory.current_task else "",
        )
    finally:
        update_agent_status("ProjectDirector", "idle")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 连接
    
    实时推送 Agent 状态和日志
    """
    await websocket.accept()
    websocket_clients.append(websocket)
    
    # 发送初始状态
    await websocket.send_json({
        "type": "connected",
        "agents": list(agent_states.values()),
    })
    
    try:
        while True:
            # 接收客户端消息（心跳等）
            data = await websocket.receive_text()
            
            # 可以处理客户端发来的命令
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
        print("📡 WebSocket 客户端断开连接")


@app.post("/task/{task_id}/confirm")
async def confirm_task(task_id: str):
    """确认执行任务"""
    return {"status": "confirmed", "task_id": task_id}


@app.post("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务"""
    return {"status": "cancelled", "task_id": task_id}


# ==================== 启动入口 ====================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
