"""Synthesizer agent: merges SQL results + stats into a plain-English grounded answer."""
import os
import json
from dotenv import load_dotenv

load_dotenv()

_SYSTEM = (
    "You are a data analyst writing a concise report. "
    "Write 2–4 sentences in plain English. "
    "Cite specific numbers from the data. "
    "If there was an error, clearly explain what failed. "
    "End your response with: 'SQL used: <the sql on one line>'"
)


def _client():
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def synthesizer_node(state: dict) -> dict:
    # Builds a grounded natural-language answer from query, SQL, results, and stats
    query = state.get("query", "")
    sql = state.get("sql", "")
    results = state.get("sql_results", [])
    stats = state.get("stats", {})
    error = state.get("error", "")

    sample_rows = results[:10]
    prompt = (
        f"User question: {query}\n\n"
        f"Generated SQL:\n{sql}\n\n"
        f"First {len(sample_rows)} result rows:\n{json.dumps(sample_rows, default=str, indent=2)}\n\n"
        f"Statistical findings:\n{json.dumps(stats, indent=2)}\n\n"
    )
    if error:
        prompt += f"Error encountered: {error}\n\n"
    prompt += "Write your answer now."

    try:
        resp = _client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        answer = resp.content[0].text.strip()
    except Exception as exc:
        answer = f"Could not generate answer: {exc}"

    return {"answer": answer}
