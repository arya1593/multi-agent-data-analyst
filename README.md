# Multi-Agent Data Analysis Platform

> Ask questions about any dataset in plain English and get back a written answer, an interactive chart, and statistical findings — no SQL or coding knowledge required.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-green)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36%2B-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude%20Sonnet%20%2F%20Haiku-blueviolet)](https://anthropic.com)

**Live demo →** [arya1593-multi-agent-data-analyst.streamlit.app](https://arya1593-multi-agent-data-analyst.streamlit.app/)

---

## What it does

Upload any CSV file (or use the built-in pizza sales demo) and ask questions like:

- *"Which city sold the most pepperoni pizzas last month?"*
- *"Show me weekly revenue trends for the last 3 months"*
- *"Are there any cities with unusually low sales?"*

The platform automatically routes your question through a pipeline of four AI agents, executes the right SQL query against your data, detects statistical patterns, and summarises everything in plain English alongside an interactive chart.

---

## Architecture

```
User (browser)
      │
      ▼
Streamlit UI  ──────────────────────── app.py
      │  POST /analyze
      ▼
FastAPI Gateway ─────────────────────  api.py
      │
      ▼
LangGraph Orchestrator ──────────────  graph.py
      │
      ├──► Router Agent        classify intent → sql | viz | stats | hybrid
      │         │
      │         ▼
      │     SQL Agent          natural language → SQL → execute (self-corrects ×3)
      │         │
      │    ┌────┴────┐
      │    ▼         ▼
      │  Viz Agent  Stats Agent        run in parallel
      │    │         │
      │    └────┬────┘
      │         ▼
      │   Synthesizer Agent    merge results → plain-English answer
      │
      ▼
Answer  +  Plotly Chart  +  Stats JSON
```

---

## Agent breakdown

| Agent | Model | Responsibility |
|---|---|---|
| **Router** | Claude Haiku | Reads the schema, classifies intent (`sql` / `viz` / `stats` / `hybrid`) |
| **SQL Agent** | Claude Sonnet | Translates the question to SQLite SQL; self-corrects up to 3 times on error |
| **Viz Agent** | Claude Sonnet | Chooses chart type and builds a Plotly JSON spec from the SQL results |
| **Stats Agent** | *(no LLM)* | Runs scipy linear regression + z-score outlier detection on the raw numbers |
| **Synthesizer** | Claude Sonnet | Combines all signals into a 2–4 sentence answer citing specific numbers |

---

## Tech stack

| Layer | Technology |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) StateGraph with parallel edges |
| AI models | Anthropic Claude Sonnet 4.6 (SQL, Viz, Synth) · Haiku 4.5 (Router) |
| API gateway | FastAPI + Uvicorn |
| Frontend | Streamlit (wide layout, `st.dialog` welcome popup) |
| Database | SQLite via SQLAlchemy (swappable via `DATABASE_URL`) |
| Charts | Plotly (rendered in-browser via `plotly.graph_objects`) |
| Statistics | SciPy (`linregress`, z-score) · Pandas |
| Deployment | Render (API) · Streamlit Community Cloud (UI) |

---

## Project structure

```
multi_agent_platform/
├── app.py                  # Streamlit UI
├── api.py                  # FastAPI gateway (analyze / upload / tables / health)
├── graph.py                # LangGraph wiring
├── seed_db.py              # Creates pizza_sales.db demo data
├── generate_qr.py          # Generates a QR code PNG for any URL
├── render.yaml             # Render.com deployment config
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── secrets.toml.example
├── agents/
│   ├── router.py
│   ├── sql_agent.py
│   ├── viz_agent.py
│   ├── stats_agent.py
│   └── synthesizer.py
└── tools/
    └── db_tools.py         # get_schema() and execute_sql()
```

---

## Local setup

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/arya1593/multi-agent-data-analyst.git
cd multi-agent-data-analyst

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# Edit .env and paste your ANTHROPIC_API_KEY

# 4. Seed the demo database (pizza sales, 500 rows, 8 cities)
python seed_db.py

# 5. Start the API server  (terminal 1)
uvicorn api:app --reload --port 8000

# 6. Start the Streamlit UI  (terminal 2)
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Using your own data

1. Click **"Load your data"** in the left sidebar.
2. Upload any `.csv` file.
3. The file is loaded into SQLite as a new table named after the filename.
4. Start asking questions about your data immediately.

> **Note:** on the free Render tier the disk resets daily, so uploaded CSVs are temporary. For persistent custom data, connect a hosted Postgres database via the `DATABASE_URL` environment variable.

---

## Demo dataset

The built-in demo contains **500 pizza orders** across 8 US cities over 6 months.

| Table | Columns |
|---|---|
| `orders` | id, city, pizza_type, quantity, sale_date, revenue |
| `locations` | city, region, manager_name |
| `products` | pizza_type, category, base_price |

**Cities:** Chicago · New York · Houston · Phoenix · Dallas · Seattle · Miami · Denver  
**Pizza types:** pepperoni · margherita · bbq_chicken · veggie · hawaiian

### Example questions to try

```
Which city sold the most pepperoni pizzas last month?
Show me weekly revenue for the last 3 months
What is the best-selling pizza type overall?
Compare revenue by region
Are there any cities with unusually low sales?
What's the average order value per pizza category?
Which manager's region has the highest revenue?
```

---

## Deployment

### Backend — Render

1. Push the repo to GitHub.
2. Create a new **Web Service** on [Render](https://render.com), pointing at this repo.
3. Render will read `render.yaml` automatically:
   - **Build command:** `pip install -r requirements.txt && python seed_db.py`
   - **Start command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Add the `ANTHROPIC_API_KEY` environment variable in the Render dashboard.

### Frontend — Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and connect your GitHub repo.
2. Set the main file path to `app.py`.
3. Under **Secrets**, add:
   ```toml
   API_URL = "https://your-render-service.onrender.com"
   ```

### QR code for sharing

```bash
pip install qrcode[pil]
python generate_qr.py https://your-streamlit-app.streamlit.app
# Saves demo_qr.png
```

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key |
| `DATABASE_URL` | No | `sqlite:///./pizza_sales.db` | SQLAlchemy connection string |
| `API_URL` | No (Streamlit) | `http://localhost:8000` | URL of the FastAPI backend |

---

## How a query flows through the system

1. User types a question in the chat box.
2. Streamlit POSTs `{"question": "..."}` to `/analyze`.
3. FastAPI calls `run_query()` which invokes the LangGraph graph.
4. **Router** (Haiku): reads the database schema + question, returns intent JSON.
5. **SQL Agent** (Sonnet): generates SQLite SQL, executes it, self-corrects on failure.
6. **Viz Agent** (Sonnet) and **Stats Agent** (scipy) run in parallel on the results.
7. **Synthesizer** (Sonnet): merges the SQL rows, chart spec, and stats into a 2–4 sentence answer.
8. FastAPI returns `{answer, sql, chart_spec, stats, error}`.
9. Streamlit renders the answer card (left) and Plotly chart (right).

---

## Built by

**Arya Patel**
