# Multi-Agent Data Analysis Platform

> Ask questions about any dataset in plain English and get back a written answer, an interactive chart, and statistical findings — no SQL or coding knowledge required.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-green)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36%2B-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-Llama%203-orange)](https://groq.com)

**Live demo →** [arya1593-multi-agent-data-analyst.streamlit.app](https://arya1593-multi-agent-data-analyst.streamlit.app/)

---

## What it does

Upload any CSV file (or use the built-in global e-commerce demo) and ask questions like:

- *"Which city has the highest total revenue?"*
- *"Show me monthly revenue trends for the last 6 months"*
- *"Which product category generates the most sales?"*

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
| **Router** | Llama 3.1 8B Instant | Reads the schema, classifies intent (`sql` / `viz` / `stats` / `hybrid`) |
| **SQL Agent** | Llama 3.3 70B Versatile | Translates the question to SQLite SQL; self-corrects up to 3 times on error |
| **Viz Agent** | Llama 3.3 70B Versatile | Chooses chart type and builds a Plotly JSON spec from the SQL results |
| **Stats Agent** | *(no LLM)* | Runs scipy linear regression + z-score outlier detection on the raw numbers |
| **Synthesizer** | Llama 3.3 70B Versatile | Combines all signals into a 2–4 sentence answer citing specific numbers |

---

## Tech stack

| Layer | Technology |
|---|---|
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) StateGraph with parallel edges |
| AI models | Groq · Llama 3.3 70B Versatile (SQL, Viz, Synth) · Llama 3.1 8B Instant (Router) |
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
- A free [Groq API key](https://console.groq.com/) (no credit card required)

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/arya1593/multi-agent-data-analyst.git
cd multi-agent-data-analyst

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# Edit .env and paste your GROQ_API_KEY

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

The built-in demo contains **600 e-commerce orders** across 15 cities in 3 global regions over 6 months.

| Table | Columns |
|---|---|
| `orders` | id, city, product_name, category, customer_segment, quantity, order_date, revenue |
| `products` | product_name, category, base_price |
| `regions` | city, country, region |

**Regions:** North America · Europe · Asia Pacific  
**Cities:** New York · Los Angeles · Chicago · Toronto · Houston · London · Paris · Berlin · Amsterdam · Madrid · Tokyo · Singapore · Sydney · Mumbai · Seoul  
**Categories:** Technology · Furniture · Office Supplies  
**Customer segments:** Consumer · Corporate · Home Office

### Example questions to try

```
Which city has the highest total revenue?
Show me monthly revenue trend for the last 6 months
What is the best-selling product overall?
Compare revenue across regions
Which product category generates the most sales?
Which customer segment spends the most?
Are there any cities with unusually low sales?
What is the average order value for Corporate customers?
Which country has the most orders?
```

---

## Deployment

### Backend — Render

1. Push the repo to GitHub.
2. Create a new **Web Service** on [Render](https://render.com), pointing at this repo.
3. Render will read `render.yaml` automatically:
   - **Build command:** `pip install -r requirements.txt && python seed_db.py`
   - **Start command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Add the `GROQ_API_KEY` environment variable in the Render dashboard (free key from [console.groq.com](https://console.groq.com)).

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
| `GROQ_API_KEY` | Yes | — | Your free Groq API key (get one at console.groq.com) |
| `DATABASE_URL` | No | `sqlite:///./pizza_sales.db` | SQLAlchemy connection string |
| `API_URL` | No (Streamlit) | `http://localhost:8000` | URL of the FastAPI backend |

---

## How a query flows through the system

1. User types a question in the chat box.
2. Streamlit POSTs `{"question": "..."}` to `/analyze`.
3. FastAPI calls `run_query()` which invokes the LangGraph graph.
4. **Router** (Llama 3.1 8B): reads the database schema + question, returns intent JSON.
5. **SQL Agent** (Llama 3.3 70B): generates SQLite SQL, executes it, self-corrects on failure.
6. **Viz Agent** (Llama 3.3 70B) and **Stats Agent** (scipy) run in parallel on the results.
7. **Synthesizer** (Llama 3.3 70B): merges the SQL rows, chart spec, and stats into a 2–4 sentence answer.
8. FastAPI returns `{answer, sql, chart_spec, stats, error}`.
9. Streamlit renders the answer card (left) and Plotly chart (right).

---

## Built by

**Arya Patel**
