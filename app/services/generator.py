from groq import Groq
from app.config import settings
from app.services.retriever import retrieve_relevant_chunks
from typing import Dict, Any

client = Groq(api_key=settings.GROQ_API_KEY)


def generate_legal_answer(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Retrieve → threshold filter → generate citation-grounded answer.
    """
    # 1. Retrieve
    retrieved_chunks = retrieve_relevant_chunks(query, top_k=top_k)

    if not retrieved_chunks or "error" in retrieved_chunks[0]:
        return {
            "answer": "I could not find any relevant legal provisions in the database.",
            "sources": [],
            "filtered_out": 0,
            "refused": True,
        }

    # 2. Threshold filter — reject weak matches BEFORE calling the LLM
    relevant_chunks = [
        c for c in retrieved_chunks
        if c["distance"] <= settings.MAX_DISTANCE_THRESHOLD
    ]
    filtered_out = len(retrieved_chunks) - len(relevant_chunks)

    if not relevant_chunks:
        return {
            "answer": (
                "I cannot find any provision in the provided legal documents that "
                "answers this question. Please rephrase or consult a broader corpus."
            ),
            "sources": [],
            "filtered_out": filtered_out,
            "refused": True,
        }

    # 3. Build context with explicit citations
    context_blocks = []
    for i, chunk in enumerate(relevant_chunks):
        meta = chunk["metadata"]
        context_blocks.append(
            f"[Source {i+1}]\n"
            f"Document: {meta.get('source')}\n"
            f"Section: {meta.get('section')}\n"
            f"Content: {chunk['text']}\n"
        )
    context_text = "\n---\n".join(context_blocks)

    # 4. Strict legal system prompt
    system_prompt = (
        "You are a precise legal assistant. Answer the user's question based ONLY on the "
        "provided legal context. If the answer is not contained in the context, reply: "
        "'I cannot find the answer in the provided documents.' "
        "Do not use outside knowledge. Do not hallucinate. "
        "Always cite the Section number and Document name in your answer "
        "(e.g., 'According to Section 3 of sample_act.txt ...')."
    )

    user_prompt = f"""Context:
{context_text}

Question: {query}

Answer:"""

    # 5. Call Groq
    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=500
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        answer = f"Error communicating with LLM: {str(e)}"

    # 6. Sources for UI
    sources = [
        {
            "source": c["metadata"]["source"],
            "section": c["metadata"]["section"],
            "heading": c["metadata"]["heading"],
            "distance": round(c["distance"], 4)
        }
        for c in relevant_chunks
    ]

    # 7. Determine confidence/refusal based on answer content
    refused = any(phrase in answer.lower() for phrase in [
        "cannot find",
        "no provision",
        "not contained",
        "not in the provided",
    ])

    return {
        "answer": answer,
        "sources": [] if refused else sources,
        "filtered_out": filtered_out,
        "refused": refused,
    }