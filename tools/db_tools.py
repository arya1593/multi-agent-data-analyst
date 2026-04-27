"""Database utility functions: schema inspection and safe SQL execution."""
from sqlalchemy import inspect, text


def get_schema(engine) -> str:
    # Reads all tables and columns via SQLAlchemy inspector, returns formatted string
    inspector = inspect(engine)
    lines = []
    for table in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns(table)]
        lines.append(f"{table}({', '.join(cols)})")
    return "\n".join(lines)


def execute_sql(engine, sql: str) -> list:
    # Executes arbitrary SQL and returns rows as list of dicts; never raises
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            keys = list(result.keys())
            rows = [dict(zip(keys, row)) for row in result.fetchmany(200)]
            return rows
    except Exception as exc:
        return [{"error": str(exc)}]
