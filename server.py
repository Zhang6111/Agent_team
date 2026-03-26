"""FastAPI Server - 为 Node.js CLI 提供 API（异步流式架构）"""
import asyncio
import json
import uuid
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
    work_dir: Optional[str] = None


class ChatStartResponse(BaseModel):
    """异步任务启动响应"""
    task_id: str
    status: str = "started"


class AgentStatus(BaseModel):
    """Agent 状态"""
    name: str
    role: str
    status: str  # idle, working, done
    current_task: Optional[str] = None


# ==================== 全局状态 ====================

director: Optional[ProjectDirector] = None
websocket_clients: List[WebSocket] = []
agent_states: dict[str, dict] = {}
current_task: Optional[str] = None
running_tasks: dict[str, asyncio.Task] = {}   # task_id -> asyncio Task


# ==================== 初始化团队 ====================

def init_agent_team():
    """初始化 Agent 团队"""
    global director

    if director is None:
        director = ProjectDirector(memory=session_memory)

        from src.agents import (
            TechLeadAgent, FrontendDeveloperAgent, BackendDeveloperAgent,
            ProductManagerAgent, ArchitectAgent, TesterAgent, DevOpsAgent,
            UIDesignerAgent, DataEngineerAgent, CodeReviewerAgent,
            BugFixerAgent, SecurityAuditorAgent, PerformanceOptimizerAgent,
            TechnicalWriterAgent,
        )

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


# ==================== WebSocket 广播 ====================

async def broadcast(data: dict):
    """广播消息给所有 WebSocket 客户端"""
    if not websocket_clients:
        return
    disconnected = []
    for client in websocket_clients:
        try:
            await client.send_json(data)
        except Exception:
            disconnected.append(client)
    for client in disconnected:
        websocket_clients.remove(client)


async def broadcast_status(extra: dict = {}):
    """广播团队状态"""
    await broadcast({
        "type": "status_update",
        "agents": list(agent_states.values()),
        "current_task": current_task,
        "timestamp": datetime.now().isoformat(),
        **extra,
    })


def update_agent_status(name: str, status: str, task: Optional[str] = None):
    """更新 Agent 状态并推送"""
    if name in agent_states:
        agent_states[name]["status"] = status
        if task is not None:
            agent_states[name]["current_task"] = task
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(broadcast_status())
        except RuntimeError:
            pass


async def push_log(message: str, level: str = "info", task_id: str = ""):
    """推送日志消息"""
    await broadcast({
        "type": "log",
        "level": level,
        "message": message,
        "task_id": task_id,
        "timestamp": datetime.now().isoformat(),
    })


# ==================== 后台执行工作流 ====================

async def run_workflow_background(task_id: str, message: str, work_dir: str):
    """后台异步执行工作流，通过 WebSocket 推送进度"""
    global current_task

    current_task = message
    update_agent_status("ProjectDirector", "working", message)
    await push_log(f"开始处理: {message[:60]}", "info", task_id)

    try:
        context_message = f"【工作目录】{work_dir}\n\n【任务】{message}"

        # 在线程池中运行同步 LLM 调用，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: director.invoke(context_message)
        )

        # 解析文件操作
        from src.cli.executor import CLIExecutor
        executor = CLIExecutor(base_dir=work_dir)
        actions = executor.parse_agent_response(response)

        # 推送完成
        await broadcast({
            "type": "task_complete",
            "task_id": task_id,
            "message": response,
            "actions": actions,
            "timestamp": datetime.now().isoformat(),
        })
        await push_log("任务完成", "success", task_id)

        # 更新记忆
        session_memory.add_user_message(message)
        session_memory.add_ai_message(response)
        session_memory.project_info["work_dir"] = work_dir
        if not session_memory.current_task:
            session_memory.start_task(message)

    except Exception as e:
        await broadcast({
            "type": "task_error",
            "task_id": task_id,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        })
        await push_log(f"任务失败: {str(e)}", "error", task_id)

    finally:
        current_task = None
        update_agent_status("ProjectDirector", "idle")
        running_tasks.pop(task_id, None)


# ==================== FastAPI 应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_agent_team()
    print("🚀 Multi-Agent Team API 已启动")
    yield
    print("👋 Multi-Agent Team API 已关闭")


app = FastAPI(
    title="Multi-Agent Team API",
    description="多 Agent 开发团队后端 API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== HTTP 路由 ====================

@app.get("/")
async def root():
    return {"name": "Multi-Agent Team API", "version": "2.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/team")
async def get_team_status():
    return {"agents": list(agent_states.values()), "current_task": current_task}


@app.post("/chat", response_model=ChatStartResponse)
async def chat(request: ChatRequest):
    """
    聊天接口 - 立即返回 task_id，工作流在后台执行
    前端通过 WebSocket 接收进度和结果
    """
    if director is None:
        raise HTTPException(status_code=500, detail="Agent 团队未初始化")

    if current_task is not None:
        raise HTTPException(status_code=429, detail="当前已有任务在执行，请等待完成")

    work_dir = request.work_dir or os.getcwd()
    task_id = str(uuid.uuid4())

    # 启动后台任务，立即返回
    bg_task = asyncio.create_task(
        run_workflow_background(task_id, request.message, work_dir)
    )
    running_tasks[task_id] = bg_task

    return ChatStartResponse(task_id=task_id, status="started")


@app.post("/execute")
async def execute_actions(request: ChatRequest):
    """执行操作指令"""
    work_dir = request.work_dir or os.getcwd()

    from src.cli.executor import CLIExecutor
    executor = CLIExecutor(base_dir=work_dir)

    actions = []
    try:
        if isinstance(request.message, str):
            data = json.loads(request.message)
            if isinstance(data, dict):
                actions = data.get("actions", [])
            elif isinstance(data, list):
                actions = data
    except (json.JSONDecodeError, ValueError):
        actions = executor.parse_agent_response(request.message)

    if not actions:
        return {"status": "no_actions", "message": "未找到操作指令"}

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


@app.post("/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消正在运行的任务"""
    bg_task = running_tasks.get(task_id)
    if bg_task:
        bg_task.cancel()
        running_tasks.pop(task_id, None)
        return {"status": "cancelled", "task_id": task_id}
    return {"status": "not_found", "task_id": task_id}


# ==================== WebSocket ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket - 实时推送 Agent 状态和任务进度"""
    await websocket.accept()
    websocket_clients.append(websocket)

    # 发送初始状态
    await websocket.send_json({
        "type": "connected",
        "agents": list(agent_states.values()),
        "current_task": current_task,
    })

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        if websocket in websocket_clients:
            websocket_clients.remove(websocket)
        print("📡 WebSocket 客户端断开连接")


# ==================== 启动入口 ====================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
