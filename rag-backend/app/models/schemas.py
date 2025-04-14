from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.config import settings  

# Input schema: when saving a chunk to DB
class DocumentEmbeddingCreate(BaseModel):
    filename: str
    chunk_id: int
    chunk_text: str
    embedding: str
class SearchResult(BaseModel):
    id: int
    filename: str
    chunk_id: int
    chunk_text: str
    score: float

    class Config:
        from_attributes = True


# Output schema: what the API returns
class DocumentEmbeddingResponse(BaseModel):
    id: int
    filename: str
    chunk_id: int
    chunk_text: str
    embedding: str  # Keep as string type - the API should convert embeddings to JSON strings before returning
    created_at: datetime

    class Config:
        from_attributes = True