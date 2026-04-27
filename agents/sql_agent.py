"""NL→SQL agent with up to 3 self-correction attempts using Sonnet."""
import os
import re
from dotenv import load_dotenv

load_dotenv()

_SYSTEM = (
    "You are a SQL expert. Write a safe, read-only SQL query for SQLite. "
    "Return ONLY the raw SQL with no markdown fences, no explanation."
)


def _client():
    # Lazy-loads Anthropic client after dotenv has run
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _engine():
    from sqlalchemy import create_engine
    return create_engine(os.environ.get("DATABASE_URL", "sqlite:///./pizza_sales.db"))


def _strip_fences(text: str) -> str:
    # Removes ```sql ... ``` or ``` ... ``` wrappers from LLM output
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _build_messages(query: str, schema: str, prev_sql: str = "", error: str = "") -> list:
    # Constructs the messages list, appending correction context when retrying
    content = f"Schema:\n{schema}\n\nQuestion: {query}"
    if prev_sql and error:
        content += f"\n\nPrevious SQL (failed):\n{prev_sql}\nError: {error}\n\nFix the SQL."
    return [{"role": "user", "content": content}]


def sql_node(state: dict) -> dict:
    # Tries up to 3 times to generate and execute valid SQL, returning rows capped at 200
    from tools.db_tools import get_schema, execute_sql
    engine = _engine()
    schema = get_schema(engine)
    query = state.get("query", "")
    sql, error, results = "", "", []

    for _ in range(3):
        try:
            msgs = _build_messages(query, schema, sql, error)
            resp = _client().messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                system=_SYSTEM,
                messages=msgs,
            )
            sql = _strip_fences(resp.content[0].text)
            results = execute_sql(engine, sql)

            if results and "error" in results[0]:
                error = results[0]["error"]
                results = []
                continue
            return {"sql": sql, "sql_results": results[:200], "error": ""}
        except Exception as exc:
            error = str(exc)

    return {
        "sql": sql,
        "sql_results": [],
        "error": "Could not generate valid SQL after 3 attempts",
    }
