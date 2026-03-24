"""FastAPI Server - 为 Node.js CLI 提供 API"""
import asyncio
import json
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
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
    work_dir: Optional[str] = None  # 工作目录


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
            ("FrontendDev", FrontendDeveloperAgent),
            ("BackendDev", BackendDeveloperAgent),
            ("CodeReviewer", CodeReviewerAgent),
            ("Tester", TesterAgent),
            ("BugFixer", BugFixerAgent),
            ("SecurityAuditor", SecurityAuditorAgent),
            ("PerformanceOptimizer", PerformanceOptimizerAgent),
            ("DevOps", DevOpsAgent),
            ("TechnicalWriter", TechnicalWriterAgent),
        ]

        for name, agent_cls in team_members:
            if name in ["FrontendDev", "BackendDev"]:
                agent = agent_cls(name=name, memory=session_memory)
            else:
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    init_agent_team()
    print("🚀 Multi-Agent Team API 已启动")
    yield
    # 关闭时
    print("👋 Multi-Agent Team API 已关闭")


app = FastAPI(
    title="Multi-Agent Team API",
    description="多 Agent 开发团队后端 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置（允许 Node.js CLI 连接）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    
    # 确定工作目录
    work_dir = request.work_dir or os.getcwd()
    
    # 更新任务
    current_task = request.message
    update_agent_status("ProjectDirector", "working", request.message)
    
    try:
        # 调用项目总监（带上工作目录上下文）
        context_message = f"""【工作目录】{work_dir}

【任务】{request.message}

请在该目录下执行任务。如果需要创建文件，请输出 JSON 格式的操作指令。"""
        
        response = director.invoke(context_message)
        
        # 解析响应中的操作指令 - 提取 JSON
        from src.cli.executor import CLIExecutor
        executor = CLIExecutor(base_dir=work_dir)
        actions = executor.parse_agent_response(response)
        
        # 更新记忆
        session_memory.add_user_message(request.message)
        session_memory.add_ai_message(response)
        session_memory.project_info["work_dir"] = work_dir
        
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


@app.post("/execute")
async def execute_actions(request: ChatRequest):
    """
    执行操作指令
    
    解析 Agent 响应并执行文件操作/命令
    """
    import json as json_lib
    
    work_dir = request.work_dir or os.getcwd()
    
    from src.cli.executor import CLIExecutor
    executor = CLIExecutor(base_dir=work_dir)
    
    # 解析操作指令 - 支持两种格式
    actions = []
    try:
        # 尝试解析 JSON 字符串
        if isinstance(request.message, str):
            data = json_lib.loads(request.message)
            if isinstance(data, dict):
                actions = data.get("actions", [])
            elif isinstance(data, list):
                actions = data
    except (json_lib.JSONDecodeError, ValueError):
        # 不是 JSON，尝试用解析器
        actions = executor.parse_agent_response(request.message)
    
    if not actions:
        return {"status": "no_actions", "message": "未找到操作指令"}
    
    # 执行操作
    results = []
    for action in actions:
        success, result = executor.execute_action(action, auto_confirm=True)
        results.append({
            "type": action.get("type"),
            "success": success,
            "result": str(result),
        })
    
    return {
        "status": "completed",
        "results": results,
        "summary": executor.get_execution_summary(),
    }


# ==================== 启动入口 ====================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
