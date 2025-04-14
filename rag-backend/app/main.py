from fastapi import FastAPI
from app.api import ingestion
from app.api import query
from app.api import document_select
from app.api import simple_upload

# Initialize FastAPI application with title
app = FastAPI(title="Document RAG API")

# Register API routers with their respective prefixes
# Ingestion router handles document upload and processing endpoints
app.include_router(ingestion.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(document_select.router, prefix="/api")
app.include_router(simple_upload.router, prefix="/api")
