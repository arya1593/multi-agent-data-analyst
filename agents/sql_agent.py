"""NL→SQL agent with up to 3 self-correction attempts using Groq."""
import os
import re
from dotenv import load_dotenv

load_dotenv()

_SYSTEM = (
    "You are a SQL expert. Write a safe, read-only SQL query for SQLite. "
    "Return ONLY the raw SQL with no markdown fences, no explanation."
)


def _client():
    from groq import Groq
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def _engine():
    from sqlalchemy import create_engine
    return create_engine(os.environ.get("DATABASE_URL", "sqlite:///./pizza_sales.db"))


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def sql_node(state: dict) -> dict:
    from tools.db_tools import get_schema, execute_sql
    engine = _engine()
    schema = get_schema(engine)
    query = state.get("query", "")
    sql, error, results = "", "", []

    for _ in range(3):
        try:
            content = f"Schema:\n{schema}\n\nQuestion: {query}"
            if sql and error:
                content += f"\n\nPrevious SQL (failed):\n{sql}\nError: {error}\n\nFix the SQL."

            resp = _client().chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=512,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": content},
                ],
            )
            sql = _strip_fences(resp.choices[0].message.content)
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
