"""Intent router: classifies a user query into sql/viz/stats/hybrid using Haiku."""
import json
import os
from dotenv import load_dotenv

load_dotenv()


def _client():
    # Lazy-loads the Anthropic client so the key is resolved after dotenv runs
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _engine():
    from sqlalchemy import create_engine
    url = os.environ.get("DATABASE_URL", "sqlite:///./pizza_sales.db")
    return create_engine(url)


def router_node(state: dict) -> dict:
    # Classifies the user query intent; defaults to 'hybrid' on parse failure
    from tools.db_tools import get_schema
    schema = get_schema(_engine())
    user_query = state.get("query", "")

    system = "You are a query router. Respond ONLY with valid JSON."
    user_msg = (
        f"Database schema:\n{schema}\n\n"
        f"User question: {user_query}\n\n"
        "Return JSON with keys: intent (sql|viz|stats|hybrid), "
        "relevant_tables (list), needs_chart (bool), needs_stats (bool)."
    )

    try:
        resp = _client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = resp.content[0].text.strip()
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
    # Returns the intent string for use as a LangGraph conditional edge
    return state.get("intent", "hybrid")
