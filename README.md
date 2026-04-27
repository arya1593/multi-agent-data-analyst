# Multi-Agent Data Analysis Platform

Ask a plain-English question about a pizza sales database and receive a grounded written answer plus an interactive Plotly chart — no SQL knowledge required. The system orchestrates four specialized AI agents (router, SQL, visualization, stats) through a LangGraph state machine.

## Architecture

```
User
 │
 ▼
Streamlit UI (app.py)
 │  HTTP POST /analyze
 ▼
FastAPI Gateway (api.py)
 │
 ▼
LangGraph Orchestrator (graph.py)
 │
 ├──► Router Agent ──► classifies intent (sql | viz | stats | hybrid)
 │         │
 │         ▼
 │     SQL Agent ──► NL→SQL→results (self-corrects up to 3×)
 │         │
 │    ┌────┴────┐
 │    ▼         ▼
 │  Viz Agent  Stats Agent   (run in parallel)
 │    │         │
 │    └────┬────┘
 │         ▼
 │    Synthesizer Agent ──► plain-English answer + SQL citation
 │
 ▼
Answer + Chart + Stats
```

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Open .env and add your ANTHROPIC_API_KEY

# 3. Seed the database
python seed_db.py

# 4. Start the API gateway (keep this terminal open)
uvicorn api:app --reload --port 8000

# 5. Launch the Streamlit UI (new terminal)
streamlit run app.py
```

Open your browser to http://localhost:8501

## Example Questions

- "Which city sold the most pepperoni pizzas last month?"
- "Show me weekly revenue for the last 3 months"
- "What is the best-selling pizza type overall?"
- "Compare revenue by region"
- "Are there any cities with unusually low sales?"
- "What's the average order value per pizza category?"
- "Which manager's region has the highest revenue?"

## Deployment Note

For a GitHub demo — deploy FastAPI on Render, Streamlit on Streamlit Community Cloud. Generate a QR code at qr.io pointing to your Streamlit URL for easy mobile sharing.
