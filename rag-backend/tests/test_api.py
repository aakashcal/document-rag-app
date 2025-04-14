import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
import json
import numpy as np
from io import BytesIO
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.core.db import DocumentEmbedding, Base, engine
from app.models.schemas import DocumentEmbeddingResponse, SearchResult

# Initialize test client
client = TestClient(app)

# Setup test database - use in-memory SQLite for testing
@pytest.fixture(scope="function")
def db_session():
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    
    # Create a new db session
    from app.core.db import SessionLocal
    db = SessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)

# Fixture to mock document embeddings in DB
@pytest.fixture
def mock_document_embeddings(test_db):
    # Create test document embeddings
    embeddings = []
    
    # Document 1 with 2 chunks
    embedding_vector = [0.1] * 1536  # Example vector with 1536 dimensions
    
    # Add as list type (new format)
    doc1_chunk1 = DocumentEmbedding(
        filename="test_doc1.pdf",
        chunk_id=0,
        chunk_text="This is test chunk 1 for document 1",
        embedding=embedding_vector,
        created_at=datetime.now()
    )
    
    doc1_chunk2 = DocumentEmbedding(
        filename="test_doc1.pdf",
        chunk_id=1,
        chunk_text="This is test chunk 2 for document 1",
        embedding=embedding_vector,
        created_at=datetime.now()
    )
    
    # Document 2 with 1 chunk - using JSON string (old format)
    doc2_chunk1 = DocumentEmbedding(
        filename="test_doc2.pdf",
        chunk_id=0,
        chunk_text="This is test chunk 1 for document 2",
        embedding=json.dumps(embedding_vector),
        created_at=datetime.now()
    )
    
    embeddings.extend([doc1_chunk1, doc1_chunk2, doc2_chunk1])
    
    # Add to database
    for emb in embeddings:
        test_db.add(emb)
    test_db.commit()
    
    return embeddings

# Test document list endpoint
def test_list_documents(client, test_db, mock_document_embeddings):
    response = client.get("/api/documents/list")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return 2 documents (each unique filename)
    assert len(data) == 2
    assert "test_doc1.pdf" in [doc["filename"] for doc in data]
    assert "test_doc2.pdf" in [doc["filename"] for doc in data]

# Test document deletion endpoint
def test_delete_document(client, test_db, mock_document_embeddings):
    # First verify we have 3 embeddings in DB
    count_before = test_db.query(DocumentEmbedding).count()
    assert count_before == 3
    
    # Delete a document
    response = client.delete("/api/documents/test_doc1.pdf")
    
    # Check status code
    assert response.status_code == 204
    
    # Verify chunks were deleted
    count_after = test_db.query(DocumentEmbedding).count()
    assert count_after == 1  # Only doc2 should remain
    
    # Verify the right document remains
    remaining_doc = test_db.query(DocumentEmbedding).first()
    assert remaining_doc.filename == "test_doc2.pdf"

# Test delete non-existent document
def test_delete_nonexistent_document(client, test_db):
    response = client.delete("/api/documents/nonexistent.pdf")
    assert response.status_code == 404

# Test document upload with mocked embedding generation
@patch("app.api.ingestion.save_uploaded_document")
@patch("app.api.ingestion.read_document_content")
@patch("app.api.ingestion.process_document")
def test_document_upload(mock_process, mock_read, mock_save, client, test_db):
    # Setup mocks
    mock_save.return_value = "uploads/test_upload.txt"
    mock_read.return_value = "This is a test document content"
    
    # Mock the embedding process
    sample_chunks = ["Chunk 1", "Chunk 2"]
    sample_embeddings = [[0.1] * 1536, [0.2] * 1536]  # Two embedding vectors
    mock_process.return_value = (sample_chunks, sample_embeddings, {"chunks": 2})
    
    # Create test file
    test_file = BytesIO(b"Test content")
    
    # Make API request
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test_upload.txt", test_file, "text/plain")}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # We should have 2 chunks in response
    assert len(data) == 2
    
    # Verify mocks were called correctly
    mock_save.assert_called_once()
    mock_read.assert_called_once()
    mock_process.assert_called_once()
    
    # Check database has the new embeddings
    uploaded_docs = test_db.query(DocumentEmbedding).filter(
        DocumentEmbedding.filename == "test_upload.txt"
    ).all()
    assert len(uploaded_docs) == 2

# Test query endpoint with mocked embedding generation and OpenAI calls
@patch("app.api.query.generate_embeddings")
@patch("app.api.query.openai_client.chat.completions.create")
def test_query_search(mock_openai, mock_embeddings, client, test_db, mock_document_embeddings):
    # Mock embedding generation for query
    mock_embeddings.return_value = [[0.1] * 1536]  # Query embedding
    
    # Mock OpenAI chat completion
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "This is a mock answer from OpenAI."
    mock_openai.return_value = mock_completion
    
    # Define query payload
    query_payload = {
        "q": "test query",
        "k": 2,
        "document_ids": ["test_doc1.pdf"],
        "include_chunks": True
    }
    
    # Make API request
    response = client.post("/api/query/search", json=query_payload)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "answer" in data
    assert data["answer"] == "This is a mock answer from OpenAI."
    
    # Check that chunks are included
    assert "chunks" in data
    
    # Verify mocks were called correctly
    mock_embeddings.assert_called_once()
    mock_openai.assert_called_once()

# Test query with embedding type mismatch error
@patch("app.api.query.generate_embeddings")
def test_query_with_embedding_type_mismatch(mock_embeddings, client, test_db):
    # Create test document with incompatible embedding format (list vs JSON string issue)
    embedding_wrong_format = DocumentEmbedding(
        filename="wrong_format.pdf",
        chunk_id=0,
        chunk_text="This is a test with wrong embedding format",
        embedding=[0.1] * 1536,  # List format
        created_at=datetime.now()
    )
    test_db.add(embedding_wrong_format)
    test_db.commit()
    
    # Mock query embedding generation with incompatible vector
    mock_embeddings.return_value = [[0.2] * 768]  # Different dimension to cause mismatch
    
    # Define query payload
    query_payload = {
        "q": "test query",
        "k": 2,
        "document_ids": ["wrong_format.pdf"],
        "include_chunks": True
    }
    
    # Make API request
    response = client.post("/api/query/search", json=query_payload)
    
    # This should return a 500 or show a helpful error about embedding mismatch
    assert response.status_code in [500, 404]
    
    # Verify the error message mentions embedding mismatch
    if response.status_code == 500:
        assert "embedding" in response.json()["detail"].lower()

# Test empty document upload
def test_empty_document_upload(client, test_db):
    # Create test file
    empty_file = BytesIO(b"")
    
    # Make API request
    response = client.post(
        "/api/documents/upload",
        files={"file": ("empty.txt", empty_file, "text/plain")}
    )
    
    # Should return a 400 error for empty content
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower() 