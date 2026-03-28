"""FastAPI Server - 为 CLI 提供 API（手动模式）"""
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

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings
from src.memory import session_memory

AGENTS = [
    ("1", "ProductManager", "产品经理 - 需求分析、PRD输出"),
    ("2", "Architect", "架构师 - 技术架构设计"),
    ("3", "DataEngineer", "数据工程师 - 数据库设计"),
    ("4", "UIDesigner", "UI设计师 - 页面布局、样式规范"),
    ("5", "FrontendDev", "前端开发 - 前端实现"),
    ("6", "BackendDev", "后端开发 - 后端实现"),
    ("7", "CodeReviewer", "代码评审 - 代码审查"),
    ("8", "Tester", "测试工程师 - 功能测试"),
    ("9", "SecurityAuditor", "安全审计 - 漏洞扫描"),
    ("0", "PerformanceOptimizer", "性能优化 - 性能调优"),
    ("-", "DevOps", "运维工程师 - 部署配置"),
    ("=", "TechnicalWriter", "技术文档 - 文档生成"),
]


class ChatRequest(BaseModel):
    message: str
    agent: Optional[str] = "ProductManager"
    session_id: Optional[str] = None
    work_dir: Optional[str] = None


class ChatResponse(BaseModel):
    agent: str
    response: str
    timestamp: str


class AgentStatus(BaseModel):
    key: str
    name: str
    description: str
    status: str = "idle"


agent_instances: dict = {}
websocket_clients: List[WebSocket] = []
agent_states: dict[str, AgentStatus] = {}


def get_agent_instance(agent_name: str):
    if agent_name in agent_instances:
        return agent_instances[agent_name]
    
    from src.agents import (
        FrontendDeveloperAgent, BackendDeveloperAgent,
        ProductManagerAgent, ArchitectAgent, TesterAgent, DevOpsAgent,
        UIDesignerAgent, DataEngineerAgent, CodeReviewerAgent,
        SecurityAuditorAgent, PerformanceOptimizerAgent, TechnicalWriterAgent,
    )
    
    agent_classes = {
        "ProductManager": ProductManagerAgent,
        "Architect": ArchitectAgent,
        "DataEngineer": DataEngineerAgent,
        "UIDesigner": UIDesignerAgent,
        "FrontendDev": FrontendDeveloperAgent,
        "BackendDev": BackendDeveloperAgent,
        "CodeReviewer": CodeReviewerAgent,
        "Tester": TesterAgent,
        "SecurityAuditor": SecurityAuditorAgent,
        "PerformanceOptimizer": PerformanceOptimizerAgent,
        "DevOps": DevOpsAgent,
        "TechnicalWriter": TechnicalWriterAgent,
    }
    
    cls = agent_classes.get(agent_name)
    if not cls:
        return None
    
    if agent_name in ["FrontendDev", "BackendDev"]:
        agent_instances[agent_name] = cls(name=agent_name, memory=session_memory)
    else:
        agent_instances[agent_name] = cls(memory=session_memory)
    
    return agent_instances[agent_name]


def init_agent_states():
    for key, name, desc in AGENTS:
        agent_states[name] = AgentStatus(
            key=key,
            name=name,
            description=desc,
            status="idle"
        )


async def broadcast(data: dict):
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_agent_states()
    print("🚀 Multi-Agent Team API 已启动 (手动模式)")
    yield
    print("👋 Multi-Agent Team API 已关闭")


app = FastAPI(
    title="Multi-Agent Team API",
    description="多 Agent 开发团队后端 API (手动模式)",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"name": "Multi-Agent Team API", "version": "3.0.0", "mode": "manual"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/agents")
async def get_agents():
    return {"agents": [s.model_dump() for s in agent_states.values()]}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    agent = get_agent_instance(request.agent)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{request.agent}' not found")
    
    agent_states[request.agent].status = "working"
    await broadcast({
        "type": "agent_status",
        "agent": request.agent,
        "status": "working",
        "timestamp": datetime.now().isoformat(),
    })
    
    try:
        context_message = request.message
        if request.work_dir:
            context_message = f"【工作目录】{request.work_dir}\n\n【任务】{request.message}"
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: agent.invoke(context_message)
        )
        
        session_memory.add_user_message(request.message)
        session_memory.add_ai_message(response)
        if not session_memory.current_task:
            session_memory.start_task(request.message)
        
        return ChatResponse(
            agent=request.agent,
            response=response,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        agent_states[request.agent].status = "idle"
        await broadcast({
            "type": "agent_status",
            "agent": request.agent,
            "status": "idle",
            "timestamp": datetime.now().isoformat(),
        })


@app.post("/execute")
async def execute_actions(request: ChatRequest):
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.append(websocket)
    
    await websocket.send_json({
        "type": "connected",
        "agents": [s.model_dump() for s in agent_states.values()],
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


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
