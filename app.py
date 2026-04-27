"""Streamlit chat UI: two-column layout with chat history, sidebar examples, and Plotly charts."""
import os
import requests
import streamlit as st
import plotly.graph_objects as go

# Streamlit Cloud → set API_URL in app secrets; local → set env var or default to localhost
try:
    _base = st.secrets["API_URL"]
except Exception:
    _base = os.environ.get("API_URL", "http://localhost:8000")
API_URL = _base.rstrip("/") + "/analyze"

EXAMPLE_QUESTIONS = [
    "Which city sold the most pepperoni pizzas last month?",
    "Show me weekly revenue for the last 3 months",
    "What is the best-selling pizza type overall?",
    "Compare revenue by region",
    "Are there any cities with unusually low sales?",
]

st.set_page_config(page_title="Data Analyst Agent", layout="wide")
st.title("Data Analyst Agent")
st.markdown("<p style='color:grey'>Ask a question about your pizza sales database</p>", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""


def run_question(question: str):
    # Calls the FastAPI backend and appends the Q&A pair to session history
    with st.spinner("Agents working…"):
        try:
            resp = requests.post(API_URL, json={"question": question}, timeout=120)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            data = {"answer": f"Error contacting API: {exc}", "sql": "", "chart_spec": {}, "stats": {}, "error": str(exc)}

    st.session_state.history.append({"question": question, "data": data})


# Sidebar: example question buttons
with st.sidebar:
    st.header("Example Questions")
    for q in EXAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

# Display previous chat history
for item in st.session_state.history:
    with st.chat_message("user"):
        st.write(item["question"])
    with st.chat_message("assistant"):
        d = item["data"]
        col_left, col_right = st.columns([55, 45])
        with col_left:
            st.markdown(
                f"<div style='background:#f0f2f6;padding:1rem;border-radius:8px'>{d.get('answer','')}</div>",
                unsafe_allow_html=True,
            )
            if d.get("sql"):
                with st.expander("SQL generated"):
                    st.code(d["sql"], language="sql")
            if d.get("stats"):
                with st.expander("Statistical findings"):
                    st.json(d["stats"])
        with col_right:
            spec = d.get("chart_spec", {})
            if spec:
                try:
                    fig = go.Figure(spec)
                    st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    st.caption("Could not render chart.")
            else:
                st.markdown("<p style='color:grey'>No chart for this query</p>", unsafe_allow_html=True)

# Handle pending question from sidebar buttons
if st.session_state.pending_question:
    q = st.session_state.pending_question
    st.session_state.pending_question = ""
    run_question(q)
    st.rerun()

# Chat input at the bottom
user_input = st.chat_input("Ask a question about your data…")
if user_input:
    run_question(user_input)
    st.rerun()
