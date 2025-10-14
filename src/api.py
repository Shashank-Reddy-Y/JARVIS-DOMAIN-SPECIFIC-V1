"""
FastAPI backend for Verimind.

This module provides a REST API with /query endpoint.
"""

from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from main import Orchestrator

app = FastAPI(title="Verimind API", description="HuggingGPT-inspired task orchestration API")

orchestrator = Orchestrator()

class QueryRequest(BaseModel):
    query: str
    max_rounds: int = 3
    threshold: float = 0.85

class QueryResponse(BaseModel):
    final_output: str
    score: float
    trace: list

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Handle query requests.
    """
    result = await orchestrator.run_task(request.query, request.max_rounds, request.threshold)
    return QueryResponse(
        final_output=result['final_output'],
        score=result['score'],
        trace=result['trace']
    )

@app.get("/")
async def root():
    return {"message": "Verimind API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
