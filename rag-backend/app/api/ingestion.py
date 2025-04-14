# FastAPI framework components for creating API routes and handling file uploads
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
# SQLAlchemy ORM session for database operations
from sqlalchemy.orm import Session
# Database session dependency injection
from app.core.db import get_db
# Pydantic schema for API response validation and serialization
from app.models.schemas import DocumentEmbeddingResponse
# Database model for storing document embeddings
from app.core.db import DocumentEmbedding
# Utilities for saving and reading document files
from app.services.storage import save_uploaded_document, read_document_content
# Document processing: text chunking and embedding generation
from app.core.embeddings import process_document
# Type annotations for improved code readability and IDE support
from typing import List
# Logging utilities for application monitoring and debugging
# import logging # Removed
# JSON handling for embedding serialization/deserialization
import json
# Custom response types for error handling with specific status codes
from fastapi.responses import JSONResponse
# Stack trace utilities for detailed error reporting
import traceback

router = APIRouter(prefix="/documents", tags=["documents"])
# logger = logging.getLogger(__name__) # Removed

@router.post("/upload", response_model=List[DocumentEmbeddingResponse])
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document for RAG integration.
    
    This endpoint:
    1. Saves the uploaded file to storage
    2. Extracts content from the document
    3. Chunks the text and generates embeddings
    4. Stores chunks and embeddings in the database
    
    Returns a list of processed document chunks with their IDs.
    """
    try:
        # Validate file type
        if not file.filename or "." not in file.filename:
            raise HTTPException(status_code=400, detail="Invalid file format")
            
        # Save and read content
        # logger.info(f"Processing file: {file.filename}") # Replaced
        # INFO: Processing file: {file.filename}
        filepath = await save_uploaded_document(file)
        content = await read_document_content(filepath)
        
        if not content or len(content.strip()) == 0:
            raise HTTPException(status_code=400, detail="Document appears to be empty")

        # Chunk + embed
        # logger.info(f"Generating chunks and embeddings for {file.filename}") # Replaced
        # INFO: Generating chunks and embeddings for {file.filename}
        chunks, embeddings, stats = await process_document(content)
        # logger.info(f"Successfully generated {len(chunks)} chunks and {len(embeddings)} embeddings") # Replaced
        # INFO: Successfully generated {len(chunks)} chunks and {len(embeddings)} embeddings
        # logger.info(f"Document stats: {stats[\'total_tokens\']} tokens, {stats[\'chunk_count\']} chunks, avg {stats[\'avg_chunk_tokens\']:.1f} tokens/chunk") # Replaced
        # INFO: Document stats: {stats['total_tokens']} tokens, {stats['chunk_count']} chunks, avg {stats['avg_chunk_tokens']:.1f} tokens/chunk

        # Insert into DB
        responses = []
        try:
            for idx, (chunk, embed) in enumerate(zip(chunks, embeddings)):
                # Ensure embedding is properly serialized as JSON
                try:
                    # Convert the raw embedding list to JSON for storage
                    embedding_json = json.dumps(embed)
                    
                    # logger.debug(f"Saving chunk {idx}: {len(chunk)} chars, embedding: {len(embed)} dimensions") # Replaced
                    # DEBUG: Saving chunk {idx}: {len(chunk)} chars, embedding: {len(embed)} dimensions
                except Exception as json_error:
                    # logger.error(f"Failed to serialize embedding: {str(json_error)}") # Replaced
                    # ERROR: Failed to serialize embedding: {str(json_error)}
                    # Fall back to string representation if JSON serialization fails
                    embedding_json = str(embed)
                
                db_obj = DocumentEmbedding(
                    filename=file.filename,
                    chunk_id=idx,
                    chunk_text=chunk,
                    embedding=embedding_json,
                )
                db.add(db_obj)
                db.flush()  # so we can get .id before commit
                responses.append(db_obj)

            # logger.info(f"Committing {len(responses)} chunks to database") # Replaced
            # INFO: Committing {len(responses)} chunks to database
            db.commit()
            # logger.info(f"Successfully committed to database") # Replaced
            # INFO: Successfully committed to database
            return responses
        except Exception as db_error:
            # logger.error(f"Database error during ingestion: {str(db_error)}") # Replaced
            # ERROR: Database error during ingestion: {str(db_error)}
            # logger.error(traceback.format_exc()) # Replaced
            # ERROR: {traceback.format_exc()}
            db.rollback()
            return JSONResponse(status_code=500, content={"detail": f"Database error: {str(db_error)}"})

    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        db.rollback()
        # logger.error(f"Error during ingestion: {str(e)}", exc_info=True) # Replaced
        # ERROR: Error during ingestion: {str(e)} # Add exc_info=True if needed for debugging
        # Return more specific error if possible
        error_detail = f"Failed to process document: {str(e)}"
        if "storage" in str(e).lower():
            return JSONResponse(status_code=500, content={"detail": "Failed to save document"})
        elif "extract" in str(e).lower():
            return JSONResponse(status_code=422, content={"detail": "Could not extract text from document"})
        elif "embedding" in str(e).lower():
            return JSONResponse(status_code=500, content={"detail": "Failed to generate embeddings"})
        else:
            return JSONResponse(status_code=500, content={"detail": error_detail})