"""Intent router: classifies a user query into sql/viz/stats/hybrid using Groq."""
import json
import os
from dotenv import load_dotenv

load_dotenv()


def _client():
    from groq import Groq
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def _engine():
    from sqlalchemy import create_engine
    url = os.environ.get("DATABASE_URL", "sqlite:///./pizza_sales.db")
    return create_engine(url)


def router_node(state: dict) -> dict:
    from tools.db_tools import get_schema
    schema = get_schema(_engine())
    user_query = state.get("query", "")

    try:
        resp = _client().chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=256,
            messages=[
                {"role": "system", "content": "You are a query router. Respond ONLY with valid JSON."},
                {"role": "user", "content": (
                    f"Database schema:\n{schema}\n\n"
                    f"User question: {user_query}\n\n"
                    "Return JSON with keys: intent (sql|viz|stats|hybrid), "
                    "relevant_tables (list), needs_chart (bool), needs_stats (bool)."
                )},
            ],
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        intent = parsed.get("intent", "hybrid")
    except Exception:
        intent = "hybrid"

    return {"intent": intent}


def route_decision(state: dict) -> str:
    return state.get("intent", "hybrid")
