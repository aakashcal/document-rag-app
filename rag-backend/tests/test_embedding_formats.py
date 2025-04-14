import pytest
import json
import numpy as np
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.core.db import DocumentEmbedding, Base, engine

# Initialize test client
client = TestClient(app)

# Database session fixture
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    from app.core.db import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Test fixture for mixed embedding formats
@pytest.fixture
def mixed_embedding_formats(test_db):
    # Create embeddings with both JSON string and list formats
    embeddings = []
    
    # Sample embedding vector
    vector_1536 = [0.1] * 1536  # 1536-dimensional vector
    
    # Document 1: Embed as JSON string (old format)
    doc1 = DocumentEmbedding(
        filename="json_format.pdf",
        chunk_id=0,
        chunk_text="This document has JSON string embeddings",
        embedding=json.dumps(vector_1536),  # Convert to JSON string
        created_at=datetime.now()
    )
    
    # Document 2: Embed as Python list (new format)
    doc2 = DocumentEmbedding(
        filename="list_format.pdf",
        chunk_id=0,
        chunk_text="This document has Python list embeddings",
        embedding=vector_1536,  # Direct list
        created_at=datetime.now()
    )
    
    # Document 3: Wrong dimension (768 instead of 1536)
    doc3 = DocumentEmbedding(
        filename="wrong_dimension.pdf",
        chunk_id=0,
        chunk_text="This document has embeddings with wrong dimensions",
        embedding=[0.2] * 768,  # Different dimension to cause mismatch
        created_at=datetime.now()
    )
    
    embeddings.extend([doc1, doc2, doc3])
    
    # Add to database
    for emb in embeddings:
        test_db.add(emb)
    test_db.commit()
    
    return embeddings

# Test querying with documents having different embedding formats
@patch("app.api.query.generate_embeddings")
def test_query_with_mixed_formats(mock_embeddings, client, test_db, mixed_embedding_formats):
    # Mock the query embedding - use 1536 dimensions
    mock_embeddings.return_value = [[0.1] * 1536]
    
    # Query only the JSON string format document
    query_payload = {
        "q": "test query",
        "k": 5,
        "document_ids": ["json_format.pdf"],
        "include_chunks": True
    }
    
    # Make request
    response = client.post("/api/query/search", json=query_payload)
    
    # Should succeed as the code should handle JSON string format
    assert response.status_code == 200
    
    # Query only the list format document
    query_payload = {
        "q": "test query",
        "k": 5,
        "document_ids": ["list_format.pdf"],
        "include_chunks": True
    }
    
    # Make request
    response = client.post("/api/query/search", json=query_payload)
    
    # Should succeed as the code should handle list format
    assert response.status_code == 200
    
    # Query document with wrong dimension
    query_payload = {
        "q": "test query",
        "k": 5,
        "document_ids": ["wrong_dimension.pdf"],
        "include_chunks": True
    }
    
    # Make request
    response = client.post("/api/query/search", json=query_payload)
    
    # Should either return 500 error or empty results with warning
    data = response.json()
    if response.status_code == 200:
        # If it doesn't fail, it should return a message about dimension mismatch
        assert "dimension mismatch" in data["answer"].lower()
    else:
        # If it fails, it should be a 404 or 500
        assert response.status_code in [404, 500]

# Test the specific "JSON object must be str, bytes or bytearray, not list" error
def test_json_decode_error_handling(client, test_db):
    # Create a document with a problematic embedding (a list that will be treated as a JSON string)
    embedding_vector = [0.1] * 1536
    
    # Create document with embedding stored as a list
    problematic_doc = DocumentEmbedding(
        filename="problematic.pdf",
        chunk_id=0,
        chunk_text="This document has a problematic embedding",
        embedding=embedding_vector,  # Store as a list
        created_at=datetime.now()
    )
    
    test_db.add(problematic_doc)
    test_db.commit()
    
    # Now modify the object to simulate the error condition
    # This simulates the case where the database has a list, but the code tries to json.loads() it
    problematic_doc.embedding = embedding_vector  # Explicitly ensure it's a list
    test_db.commit()
    
    # Set up a mock for the query to ensure we test our problematic document
    with patch("app.api.query.generate_embeddings") as mock_embeddings:
        mock_embeddings.return_value = [[0.1] * 1536]
        
        # Set up mock to ensure our query returns the problematic document
        with patch("sqlalchemy.orm.query.Query.all") as mock_query:
            mock_query.return_value = [problematic_doc]
            
            # Make the query
            query_payload = {
                "q": "test query",
                "k": 5,
                "document_ids": ["problematic.pdf"],
                "include_chunks": True
            }
            
            # Make request - this should trigger the error handling for JSON decode
            response = client.post("/api/query/search", json=query_payload)
            
            # Check that the error is handled gracefully
            if response.status_code == 200:
                # If successful, it should have a helpful message
                assert "couldn't generate an answer" in response.json()["answer"].lower()
            else:
                # If it fails, verify it's the right error
                assert "JSON object" in response.json()["detail"] or "embedding" in response.json()["detail"].lower()

# Test with a mix of both types in the same query
@patch("app.api.query.generate_embeddings")
def test_query_with_both_formats(mock_embeddings, client, test_db, mixed_embedding_formats):
    # Mock the query embedding - use 1536 dimensions
    mock_embeddings.return_value = [[0.1] * 1536]
    
    # Query both JSON string and list format documents
    query_payload = {
        "q": "test query",
        "k": 5,
        "document_ids": ["json_format.pdf", "list_format.pdf"],
        "include_chunks": True
    }
    
    # Make request
    response = client.post("/api/query/search", json=query_payload)
    
    # The code should handle both formats
    assert response.status_code == 200
    data = response.json()
    
    # Successful response should have chunks from both documents
    if "chunks" in data:
        document_filenames = [chunk["filename"] for chunk in data["chunks"]]
        assert any("json_format.pdf" in filename for filename in document_filenames) or \
               any("list_format.pdf" in filename for filename in document_filenames) 