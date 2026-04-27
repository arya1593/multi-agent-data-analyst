"""FastAPI gateway: /analyze, /upload, /tables, and /health endpoints."""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from graph import run_query
from tools.db_tools import get_schema

app = FastAPI(title="Multi-Agent Data Analysis Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _engine():
    url = os.environ.get("DATABASE_URL", "sqlite:///./pizza_sales.db")
    return create_engine(url)


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


@app.get("/tables")
def tables():
    # Returns the current database schema so the UI can show what data is loaded
    try:
        schema = get_schema(_engine())
        return {"schema": schema}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    # Accepts a CSV file, loads it into SQLite as a new table named after the file
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        # Sanitise table name: lowercase, spaces → underscores, strip .csv
        table_name = (
            file.filename.lower()
            .replace(".csv", "")
            .replace(" ", "_")
            .replace("-", "_")
        )
        df.to_sql(table_name, _engine(), if_exists="replace", index=False)
        return {
            "table": table_name,
            "rows": len(df),
            "columns": list(df.columns),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # Runs the full LangGraph pipeline and returns structured results
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
