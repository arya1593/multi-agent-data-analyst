"""Streamlit chat UI with welcome popup, CSV uploader, and two-column results."""
import os
import requests
import streamlit as st
import plotly.graph_objects as go

try:
    _base = st.secrets["API_URL"]
except Exception:
    _base = os.environ.get("API_URL", "http://localhost:8000")
API_BASE = _base.rstrip("/")

EXAMPLES = [
    "Which city sold the most pepperoni pizzas last month?",
    "Show me weekly revenue for the last 3 months",
    "What is the best-selling pizza type overall?",
    "Compare revenue by region",
    "Are there any cities with unusually low sales?",
]

st.set_page_config(page_title="Data Analyst Agent", layout="wide")

if "history"          not in st.session_state: st.session_state.history          = []
if "pending_question" not in st.session_state: st.session_state.pending_question = ""
if "loaded_tables"    not in st.session_state: st.session_state.loaded_tables    = None
if "show_welcome"     not in st.session_state: st.session_state.show_welcome     = True


@st.dialog("Welcome to Data Analyst Agent!")
def welcome_popup():
    st.markdown(
        "This app lets you ask questions about data **in plain English** — no coding needed.\n\n"
        "---\n\n"
        "**To get started:**\n\n"
        "1. The app already has **pizza sales demo data** loaded — you can start asking right away.\n"
        "2. Or upload your **own CSV file** in the left sidebar under *Load your data*.\n\n"
        "---\n\n"
        "**Try this example question:**\n\n"
        "> *Which city sold the most pepperoni pizzas last month?*\n\n"
        "Type it in the box at the bottom of the screen, or click any button on the left.\n\n"
        "---\n\n"
        "You will get a plain-English **answer**, a **chart**, and optionally the SQL query used."
    )
    if st.button("Got it, let's go!", use_container_width=True, type="primary"):
        st.session_state.show_welcome = False
        st.rerun()


def fetch_tables() -> str:
    try:
        r = requests.get(f"{API_BASE}/tables", timeout=10)
        return r.json().get("schema", "")
    except Exception:
        return ""


def run_question(question: str):
    with st.spinner("Agents working — usually 5 to 15 seconds..."):
        try:
            r = requests.post(f"{API_BASE}/analyze", json={"question": question}, timeout=120)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            data = {"answer": f"Could not reach the server. Please wait 30 seconds and try again.\n\nDetail: {exc}",
                    "sql": "", "chart_spec": {}, "stats": {}, "error": str(exc)}
    st.session_state.history.append({"question": question, "data": data})


def render_result(d: dict):
    col_left, col_right = st.columns([55, 45])
    with col_left:
        st.markdown(
            f"<div style='background:#f0f2f6;padding:1rem 1.2rem;border-radius:10px;"
            f"font-size:1rem;line-height:1.6'>{d.get('answer','')}</div>",
            unsafe_allow_html=True,
        )
        if d.get("sql"):
            with st.expander("See the SQL query that was used"):
                st.code(d["sql"], language="sql")
        if d.get("stats"):
            with st.expander("See statistical findings"):
                st.json(d["stats"])
    with col_right:
        spec = d.get("chart_spec", {})
        if spec:
            try:
                st.plotly_chart(go.Figure(spec), use_container_width=True)
            except Exception:
                st.caption("Chart could not be rendered for this result.")
        else:
            st.markdown(
                "<p style='color:#aaa;margin-top:60px;text-align:center'>"
                "No chart for this question</p>", unsafe_allow_html=True
            )


# Show welcome popup on first visit
if st.session_state.show_welcome:
    welcome_popup()


# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Data Analyst Agent")
    st.caption("Ask questions about any data — no technical skills needed.")
    st.divider()

    # CSV Upload
    st.subheader("1. Load your data")
    st.markdown(
        "Upload any **CSV file** (a spreadsheet saved as .csv) and "
        "the app will let you ask questions about it instantly."
    )
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"], label_visibility="collapsed")
    if uploaded:
        with st.spinner(f"Loading {uploaded.name}..."):
            try:
                r = requests.post(
                    f"{API_BASE}/upload",
                    files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
                    timeout=30,
                )
                r.raise_for_status()
                info = r.json()
                st.success(
                    f"Loaded **{info['table']}**  \n"
                    f"{info['rows']} rows · {len(info['columns'])} columns  \n"
                    f"Columns: {', '.join(info['columns'])}"
                )
                st.session_state.loaded_tables = fetch_tables()
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

    st.markdown("*Or use the built-in demo data (pizza sales across 8 US cities).*")
    st.divider()

    # Example questions
    st.subheader("2. Try an example")
    for q in EXAMPLES:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

    # Show what's in the database
    st.divider()
    with st.expander("What data is loaded?"):
        schema = st.session_state.loaded_tables or fetch_tables()
        if schema:
            for line in schema.strip().split("\n"):
                st.markdown(f"- `{line}`")
        else:
            st.caption("Could not reach the server yet.")

    # Name credit
    st.divider()
    st.markdown(
        "<div style='text-align:center;color:#888;font-size:0.82rem;padding-bottom:0.5rem'>"
        "Built by <strong>Arya Patel</strong></div>",
        unsafe_allow_html=True,
    )


# ── MAIN AREA ───────────────────────────────────────────────────────────────
st.markdown("## Ask a question about your data")
st.caption("Type in plain English — no SQL or coding knowledge needed.")

# Welcome card shown only before the first question
if not st.session_state.history:
    st.info(
        "**How to get started**\n\n"
        "1. **(Optional)** Upload your own CSV file in the left sidebar — or skip this and use the built-in pizza sales demo data.\n\n"
        "2. **Ask a question** — type it in the box below, or click one of the example buttons on the left.\n\n"
        "3. **Read your answer** — you'll get a plain-English summary and a chart on the right."
    )

# Chat history
for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        render_result(item["data"])

# Sidebar button fires a question
if st.session_state.pending_question:
    q = st.session_state.pending_question
    st.session_state.pending_question = ""
    run_question(q)
    st.rerun()

# Chat input
user_input = st.chat_input("Type your question here, e.g. 'Which city had the highest revenue?'")
if user_input:
    run_question(user_input)
    st.rerun()
