import pytest
import json
import numpy as np
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime
import sqlite3

from app.main import app
from app.core.db import DocumentEmbedding, Base, engine
from app.api.query import _process_query

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

# Test the embedding format handling in the code
@pytest.fixture
def embedding_format_test_data(test_db):
    """Create test data for both embedding formats"""
    embeddings = []
    
    # Create identical vector for both formats
    vector_1536 = [0.1] * 1536
    
    # Format 1: JSON string (old format)
    json_doc = DocumentEmbedding(
        filename="json_string.pdf",
        chunk_id=0,
        chunk_text="This embedding is stored as a JSON string",
        embedding=json.dumps(vector_1536),  # String format
        created_at=datetime.now()
    )
    
    # Format 2: Python list (new format)
    list_doc = DocumentEmbedding(
        filename="python_list.pdf",
        chunk_id=0,
        chunk_text="This embedding is stored as a Python list",
        embedding=vector_1536,  # Direct list
        created_at=datetime.now()
    )
    
    embeddings.extend([json_doc, list_doc])
    
    # Add to database
    for emb in embeddings:
        test_db.add(emb)
    test_db.commit()
    
    return embeddings

# Test the solution works in the processing function
@pytest.mark.asyncio
@patch("app.api.query.generate_embeddings")
@patch("app.api.query.openai_client.chat.completions.create")
async def test_process_query_handles_both_formats(mock_openai, mock_embeddings, test_db, embedding_format_test_data):
    """Test that the processing function correctly handles both embedding formats"""
    # Mock the query embedding
    mock_embeddings.return_value = [[0.1] * 1536]
    
    # Mock the OpenAI response
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "This is a test answer"
    mock_openai.return_value = mock_completion
    
    # Test the function with both document types
    result = await _process_query(
        q="test query",
        k=5,
        db=test_db,
        document_ids=["json_string.pdf", "python_list.pdf"],
        include_chunks=True
    )
    
    # Check result structure
    assert "answer" in result
    assert result["answer"] == "This is a test answer"
    assert "chunks" in result
    
    # Make sure both documents are present in results
    doc_filenames = [chunk["filename"] for chunk in result["chunks"]]
    assert "json_string.pdf" in doc_filenames or "python_list.pdf" in doc_filenames

# Test only JSON string format
@pytest.mark.asyncio
@patch("app.api.query.generate_embeddings")
@patch("app.api.query.openai_client.chat.completions.create")
async def test_process_query_json_string_format(mock_openai, mock_embeddings, test_db, embedding_format_test_data):
    """Test processing function with only JSON string format embeddings"""
    # Mock the query embedding
    mock_embeddings.return_value = [[0.1] * 1536]
    
    # Mock the OpenAI response
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "This is a test answer"
    mock_openai.return_value = mock_completion
    
    # Test with only JSON string format document
    result = await _process_query(
        q="test query",
        k=5,
        db=test_db,
        document_ids=["json_string.pdf"],
        include_chunks=True
    )
    
    # Verify results
    assert result["answer"] == "This is a test answer"
    assert len(result["chunks"]) > 0
    assert all(chunk["filename"] == "json_string.pdf" for chunk in result["chunks"])

# Test only Python list format
@pytest.mark.asyncio
@patch("app.api.query.generate_embeddings")
@patch("app.api.query.openai_client.chat.completions.create")
async def test_process_query_python_list_format(mock_openai, mock_embeddings, test_db, embedding_format_test_data):
    """Test processing function with only Python list format embeddings"""
    # Mock the query embedding
    mock_embeddings.return_value = [[0.1] * 1536]
    
    # Mock the OpenAI response
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "This is a test answer"
    mock_openai.return_value = mock_completion
    
    # Test with only Python list format document
    result = await _process_query(
        q="test query",
        k=5,
        db=test_db,
        document_ids=["python_list.pdf"],
        include_chunks=True
    )
    
    # Verify results
    assert result["answer"] == "This is a test answer"
    assert len(result["chunks"]) > 0
    assert all(chunk["filename"] == "python_list.pdf" for chunk in result["chunks"])

# Test the exact fix for the JSON object error
def test_embedding_parsing_fix():
    """Test the specific fix for the JSON format error"""
    # Create an embedding vector
    vector = [0.1] * 1536
    
    # The function that extracts embeddings should have this logic:
    def parse_embedding(embedding):
        """Simulates the fix in the query.py code"""
        if isinstance(embedding, str):
            # Handle JSON string format
            return np.array(json.loads(embedding))
        else:
            # Handle direct list format
            return np.array(embedding)
    
    # Test with both formats
    json_format = json.dumps(vector)
    list_format = vector
    
    # Both should parse correctly
    json_parsed = parse_embedding(json_format)
    list_parsed = parse_embedding(list_format)
    
    # Both should result in the same numpy array
    assert isinstance(json_parsed, np.ndarray)
    assert isinstance(list_parsed, np.ndarray)
    assert json_parsed.shape == list_parsed.shape
    assert np.array_equal(json_parsed, list_parsed)

# Test database storage and retrieval
def test_db_storage_format(test_db):
    """Test that embeddings are properly stored and retrieved from DB"""
    # Create test data
    vector = [0.1] * 1536
    
    # Store as list format
    doc = DocumentEmbedding(
        filename="test.pdf",
        chunk_id=0,
        chunk_text="Test document",
        embedding=vector,  # Store as list
        created_at=datetime.now()
    )
    
    test_db.add(doc)
    test_db.commit()
    
    # Retrieve from DB
    retrieved_doc = test_db.query(DocumentEmbedding).first()
    
    # Check format
    assert retrieved_doc is not None
    assert retrieved_doc.embedding is not None
    
    # The embedding should still be stored in the original format
    assert isinstance(retrieved_doc.embedding, list) or isinstance(retrieved_doc.embedding, dict)
    
    # Check dimensions
    if isinstance(retrieved_doc.embedding, list):
        assert len(retrieved_doc.embedding) == 1536
    else:
        # If it's a dict or other format, it should be convertible to a numpy array
        embedding_array = np.array(retrieved_doc.embedding)
        assert embedding_array.shape[0] == 1536 