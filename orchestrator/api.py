"""
Orchestrator HTTP API 服务

基于 FastAPI 提供 HTTP 接口
"""
import os
import sys
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 添加上层目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrator.main import Orchestrator, get_orchestrator


# === 请求/响应模型 ===

class ChatRequest(BaseModel):
    agent: str
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent: str


class ToolCallRequest(BaseModel):
    tool_name: str
    input_data: dict


class ToolCallResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None


# === FastAPI 应用 ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    app.state.orchestrator = get_orchestrator()
    yield
    # 关闭时清理
    await app.state.orchestrator.close()


app = FastAPI(
    title="Universal Claude Orchestrator API",
    description="ECC + claw-code 统一编排接口",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === API 端点 ===

@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "service": "Universal Claude Orchestrator",
        "version": "1.0.0"
    }


@app.get("/agents")
async def list_agents():
    """列出所有可用的 Agent"""
    orch = get_orchestrator()
    return {
        "agents": orch.list_agents()
    }


@app.get("/tools")
async def list_tools():
    """列出所有可用的工具"""
    orch = get_orchestrator()
    return {
        "tools": orch.list_tools()
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """与 Agent 对话"""
    orch = get_orchestrator()
    
    # 检查 agent 是否存在
    if req.agent not in orch.list_agents():
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{req.agent}' not found"
        )
    
    try:
        response = await orch.run(
            agent_name=req.agent,
            user_input=req.message,
            session_id=req.session_id
        )
        
        return ChatResponse(
            response=response,
            session_id=req.session_id,
            agent=req.agent
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tool", response_model=ToolCallResponse)
async def call_tool(req: ToolCallRequest):
    """直接调用工具"""
    orch = get_orchestrator()
    
    if not orch.tool_registry:
        raise HTTPException(status_code=500, detail="Tool registry not initialized")
    
    result = orch.tool_registry.execute(req.tool_name, req.input_data)
    
    return ToolCallResponse(
        success=result.success,
        output=result.output,
        error=result.error
    )


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """清除会话历史"""
    orch = get_orchestrator()
    orch.executor.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取会话历史"""
    orch = get_orchestrator()
    history = orch.executor.get_session_history(session_id)
    return {"session_id": session_id, "history": history}


# === 启动命令 ===
# uvicorn orchestrator.api:app --host 0.0.0.0 --port 8000 --reload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
