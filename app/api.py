"""
FastAPI backend for the Multi-Agent Business Research Assistant.
Provides REST API endpoints with SSE (Server-Sent Events) for real-time updates.
"""

import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
from datetime import datetime

from app.graph import run_graph
from app.utils.logger import clear_logs, get_logs

app = FastAPI(
    title="Velora Research API",
    description="Multi-Agent Business Research Assistant API",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (use Redis in production)
sessions = {}


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    max_results: int = 5


class SessionResponse(BaseModel):
    session_id: str
    messages: list[dict]
    company_name: str


@app.get("/")
async def root():
    return {
        "name": "Velora Research API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/session/create")
async def create_session():
    """Create a new conversation session."""
    import uuid
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "messages": [],
        "company_name": "",
        "created_at": datetime.utcnow().isoformat()
    }
    return {"session_id": session_id}


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session data."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "deleted"}


@app.post("/api/query")
async def query_research(request: QueryRequest):
    """
    Execute research query and return results.
    Non-streaming endpoint for simple requests.
    """
    session_id = request.session_id
    if not session_id:
        # Create new session
        import uuid
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "messages": [],
            "company_name": "",
            "created_at": datetime.utcnow().isoformat()
        }
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    # Add user message
    session["messages"].append({"role": "user", "content": request.query})
    
    # Set max results
    os.environ["MAX_SEARCH_RESULTS"] = str(request.max_results)
    
    try:
        # Run the graph
        result = run_graph(
            user_query=request.query,
            messages=session["messages"],
            company_name=session.get("company_name", "")
        )
        
        # Update session
        if result.get("company_name"):
            session["company_name"] = result["company_name"]
        
        # Add assistant message
        final_answer = result.get("final_answer", "")
        if final_answer:
            session["messages"].append({"role": "assistant", "content": final_answer})
        
        return {
            "session_id": session_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/query/stream")
async def query_research_stream(query: str, session_id: Optional[str] = None, max_results: int = 5):
    """
    Execute research query with Server-Sent Events for real-time updates.
    Streams agent progress and final results.
    """
    if not session_id:
        # Create new session
        import uuid
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "messages": [],
            "company_name": "",
            "created_at": datetime.utcnow().isoformat()
        }
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def event_generator():
        session = sessions[session_id]
        
        # Add user message
        session["messages"].append({"role": "user", "content": query})
        
        # Send initial event
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
        
        # Set max results
        os.environ["MAX_SEARCH_RESULTS"] = str(max_results)
        
        try:
            # Send initial state
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'clarity', 'status': 'analyzing query'})}\n\n"
            
            from app.graph import build_graph, AgentState
            from app.utils.logger import clear_logs, get_logs
            clear_logs()
            
            graph = build_graph()
            state: AgentState = {
                "messages": session["messages"],
                "user_query": query,
                "company_name": session.get("company_name", ""),
                "clarity_status": "",
                "clarification_question": "",
                "spellcheck_result": None,
                "research_findings": None,
                "confidence_score": 0,
                "validation_result": "",
                "validation_notes": "",
                "attempts": 0,
                "final_answer": "",
                "agent_outputs": {},
                "agent_logs": [],
                "error_log": [],
            }
            
            # Track which agents have been started to avoid duplicates
            started_agents = set()
            
            async for output in graph.astream(state, stream_mode="updates"):
                for node_name, state_update in output.items():
                    # Safely merge state updates
                    for k, v in state_update.items():
                        if k == "agent_outputs":
                            state["agent_outputs"].update(v)
                        else:
                            state[k] = v
                    
                    outs = state.get("agent_outputs", {})
                    
                    if node_name == "clarity":
                        yield f"data: {json.dumps({'type': 'agent_complete', 'agent': 'clarity', 'output': outs.get('clarity_agent', {})})}\n\n"
                        await asyncio.sleep(0.1)  # Small delay for UI update
                        
                        # Only move to research if clarity dictates it
                        if state.get("clarity_status") != "needs_clarification" and "research" not in started_agents:
                            started_agents.add("research")
                            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'research', 'status': 'searching sources'})}\n\n"
                            await asyncio.sleep(0.1)
                            
                    elif node_name == "research":
                        yield f"data: {json.dumps({'type': 'agent_complete', 'agent': 'research', 'output': outs.get('research_agent', {})})}\n\n"
                        await asyncio.sleep(0.1)
                        
                        # Determine next agent based on confidence
                        confidence = state.get("confidence_score", 0)
                        from app.config import CONFIDENCE_THRESHOLD
                        
                        if confidence < CONFIDENCE_THRESHOLD and "validator" not in started_agents:
                            started_agents.add("validator")
                            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'validator', 'status': 'validating findings'})}\n\n"
                            await asyncio.sleep(0.1)
                        elif confidence >= CONFIDENCE_THRESHOLD and "synthesis" not in started_agents:
                            # Skip validator, go straight to synthesis
                            started_agents.add("synthesis")
                            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'synthesis', 'status': 'generating report'})}\n\n"
                            await asyncio.sleep(0.1)
                        
                    elif node_name == "validator":
                        yield f"data: {json.dumps({'type': 'agent_complete', 'agent': 'validator', 'output': outs.get('validator_agent', {})})}\n\n"
                        await asyncio.sleep(0.1)
                        
                        # Validator routes back to research or forward to synthesis
                        validation = state.get("validation_result", "sufficient")
                        attempts = state.get("attempts", 0)
                        
                        if validation == "insufficient" and attempts < 3 and "research" not in started_agents:
                            started_agents.add("research")
                            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'research', 'status': 'gathering deeper sources'})}\n\n"
                            await asyncio.sleep(0.1)
                        elif "synthesis" not in started_agents:
                            started_agents.add("synthesis")
                            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'synthesis', 'status': 'generating report'})}\n\n"
                            await asyncio.sleep(0.1)
                            
                    elif node_name == "synthesis":
                        yield f"data: {json.dumps({'type': 'agent_complete', 'agent': 'synthesis', 'output': outs.get('synthesis_agent', {})})}\n\n"
                        await asyncio.sleep(0.1)
            
            state["agent_logs"] = get_logs()
            
            # Update session
            if state.get("company_name"):
                session["company_name"] = state["company_name"]
            
            # Add assistant message
            final_answer = state.get("final_answer", "")
            if final_answer:
                session["messages"].append({"role": "assistant", "content": final_answer})
            
            # Send final result
            yield f"data: {json.dumps({'type': 'complete', 'result': dict(state)})}\n\n"
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
