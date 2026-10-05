import streamlit as st

st.set_page_config(
    page_title="Legal RAG Chatbot",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Legal RAG Chatbot")
st.caption("Level 0 skeleton — RAG pipeline not connected yet.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask a legal question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        reply = (
            "Level 0 is working. "
            "Next we will add legal document ingestion, chunking, embeddings, "
            "retrieval, and citation-grounded generation."
        )
        st.write(reply)

    st.session_state.messages.append(
        {"role": "assistant", "content": reply}
    )