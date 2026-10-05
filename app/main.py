from fastapi import FastAPI
from app.config import settings


app = FastAPI(title=settings.APP_NAME)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "env": settings.ENV,
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "vector_db": settings.VECTOR_DB,
        "llm_provider": settings.LLM_PROVIDER
    }