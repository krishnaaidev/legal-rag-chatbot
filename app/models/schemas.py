from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User's legal question")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of chunks to retrieve")


class SourceItem(BaseModel):
    source: str
    section: str
    heading: Optional[str] = None
    distance: float


class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceItem]
    filtered_out: int = 0
    model: str
    refused: bool = False


class HealthResponse(BaseModel):
    status: str
    vector_db: str
    llm_provider: str
    llm_model: str