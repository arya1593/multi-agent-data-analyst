"""FastAPI gateway: exposes /analyze and /health endpoints."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import run_query

app = FastAPI(title="Multi-Agent Data Analysis Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    question: str


class AnalyzeResponse(BaseModel):
    answer:     str
    sql:        str
    chart_spec: dict
    stats:      dict
    error:      str


@app.get("/health")
def health():
    # Simple liveness check
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # Runs the full LangGraph pipeline for a user question and returns structured results
    try:
        result = run_query(req.question)
        return AnalyzeResponse(
            answer=result.get("answer", ""),
            sql=result.get("sql", ""),
            chart_spec=result.get("chart_spec", {}),
            stats=result.get("stats", {}),
            error=result.get("error", ""),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
