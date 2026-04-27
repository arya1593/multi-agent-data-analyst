"""Visualization agent: converts SQL results into a Plotly figure dict via Groq."""
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

_SYSTEM = (
    "You are a data visualization expert. "
    "Given column info and sample data, return ONLY a valid Plotly figure JSON. "
    "No markdown fences, no explanation — raw JSON only.\n"
    "Chart selection rules:\n"
    "- date/time column + numeric → line chart\n"
    "- one categorical + one numeric, ≤15 categories → bar chart\n"
    "- two numeric columns → scatter plot\n"
    "- single numeric column → histogram"
)


def _client():
    from groq import Groq
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def _fallback_chart(df) -> dict:
    import plotly.express as px
    date_cols = [c for c in df.columns if "date" in c.lower() or "week" in c.lower()]
    num_cols = df.select_dtypes("number").columns.tolist()
    cat_cols = df.select_dtypes("object").columns.tolist()

    if date_cols and num_cols:
        fig = px.line(df, x=date_cols[0], y=num_cols[0])
    elif cat_cols and num_cols:
        fig = px.bar(df, x=cat_cols[0], y=num_cols[0])
    elif len(num_cols) >= 2:
        fig = px.scatter(df, x=num_cols[0], y=num_cols[1])
    elif num_cols:
        fig = px.histogram(df, x=num_cols[0])
    else:
        fig = px.bar(df, x=df.columns[0], y=df.columns[1] if len(df.columns) > 1 else df.columns[0])
    return fig.to_dict()


def viz_node(state: dict) -> dict:
    import pandas as pd
    results = state.get("sql_results", [])
    if not results:
        return {"chart_spec": {}}

    df = pd.DataFrame(results)
    sample = df.head(5).to_string(index=False)
    col_info = {c: str(df[c].dtype) for c in df.columns}

    prompt = (
        f"Columns and dtypes: {col_info}\n"
        f"Sample rows:\n{sample}\n\n"
        f"User question: {state.get('query', '')}\n\n"
        "Return the Plotly figure JSON."
    )

    try:
        resp = _client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2048,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        chart_spec = json.loads(raw)
    except Exception:
        chart_spec = _fallback_chart(df)

    return {"chart_spec": chart_spec}
