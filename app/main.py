from fastapi import FastAPI, HTTPException
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse, SourceItem, HealthResponse
from app.services.generator import generate_legal_answer


app = FastAPI(
    title=settings.APP_NAME,
    description="Retrieval-Augmented Generation chatbot for legal documents",
    version="0.1.0"
)


@app.get("/", tags=["root"])
def root():
    return {
        "app": settings.APP_NAME,
        "env": settings.ENV,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    return HealthResponse(
        status="ok",
        vector_db=settings.VECTOR_DB,
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.LLM_MODEL
    )


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(request: ChatRequest):
    """
    Main RAG endpoint. Takes a legal question, retrieves relevant
    provisions, generates a citation-grounded answer.
    """
    try:
        result = generate_legal_answer(request.query, top_k=request.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {str(e)}")

    sources = [
        SourceItem(
            source=s["source"],
            section=s["section"],
            heading=s.get("heading"),
            distance=s["distance"]
        )
        for s in result.get("sources", [])
    ]

    return ChatResponse(
        query=request.query,
        answer=result["answer"],
        sources=sources,
        filtered_out=result.get("filtered_out", 0),
        model=settings.LLM_MODEL,
        refused=result.get("refused", False)
    )