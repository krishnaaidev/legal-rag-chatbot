import streamlit as st
import requests
from typing import Dict, Any

# Backend API URL
API_URL = "http://localhost:8000"

# ---------- Page Config ----------
st.set_page_config(
    page_title="Legal RAG Chatbot",
    page_icon="⚖️",
    layout="wide"
)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Slider for retrieval depth
    top_k = st.slider(
        "Number of chunks to retrieve", 
        min_value=1, 
        max_value=10, 
        value=3,
        help="Higher values give the LLM more context but may introduce noise."
    )
    
    st.markdown("---")

    # Backend Health Check
    try:
        health = requests.get(f"{API_URL}/health", timeout=3).json()
        st.success("Backend: Connected")
        st.caption(f"**Model:** `{health.get('llm_model', 'unknown')}`")
        st.caption(f"**Vector DB:** `{health.get('vector_db', 'unknown')}`")
    except Exception:
        st.error("Backend: Offline")
        st.caption("Start the API with:")
        st.code("uvicorn app.main:app --reload --port 8000", language="bash")

    st.markdown("---")
    
    # Clear Conversation Button
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ---------- Main UI ----------
st.title("⚖️ Legal RAG Chatbot")
st.caption("Citation-grounded answers from your legal corpus.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Render existing chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Show warning if the assistant refused to answer
        if msg["role"] == "assistant" and msg.get("refused"):
            st.warning(msg["content"])
        else:
            st.markdown(msg["content"])
            
        # Show sources expander (only if they exist and it wasn't a refusal)
        if msg["role"] == "assistant" and msg.get("sources") and not msg.get("refused"):
            with st.expander(f"📚 Sources ({len(msg['sources'])})"):
                for s in msg["sources"]:
                    st.markdown(
                        f"**{s['source']} — Section {s['section']}**  \n"
                        f"*{s.get('heading', '')}*  \n"
                        f"Relevance distance: `{s['distance']}`"
                    )

# ---------- Chat Input ----------
if prompt := st.chat_input("Ask a legal question..."):
    # 1. Append user message and render it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Call the backend API
    with st.chat_message("assistant"):
        with st.spinner("Retrieving provisions and generating answer..."):
            try:
                resp = requests.post(
                    f"{API_URL}/chat",
                    json={"query": prompt, "top_k": top_k},
                    timeout=60
                )
                resp.raise_for_status()
                data: Dict[str, Any] = resp.json()
                
                answer = data["answer"]
                sources = data.get("sources", [])
                refused = data.get("refused", False)
                filtered = data.get("filtered_out", 0)
                
            except requests.exceptions.ConnectionError:
                answer = "⚠️ Cannot reach the backend. Is Uvicorn running on port 8000?"
                sources, refused, filtered = [], False, 0
            except Exception as e:
                answer = f"⚠️ Error: {str(e)}"
                sources, refused, filtered = [], False, 0

        # 3. Render the answer based on confidence
        if refused:
            st.warning(answer)
        else:
            st.markdown(answer)

        # 4. Render sources (if applicable)
        if sources and not refused:
            with st.expander(f"📚 Sources ({len(sources)})"):
                for s in sources:
                    st.markdown(
                        f"**{s['source']} — Section {s['section']}**  \n"
                        f"*{s.get('heading', '')}*  \n"
                        f"Relevance distance: `{s['distance']}`"
                    )
                    
        # 5. Show filtered-out notice
        if filtered > 0:
            st.caption(f"ℹ️ {filtered} weak match(es) were filtered out by the relevance threshold.")

    # 6. Save assistant message to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "refused": refused
    })