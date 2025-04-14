# FastAPI framework components for creating API routes and handling file uploads
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request, status
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
import logging
# JSON handling for embedding serialization/deserialization
import json
# Custom response types for error handling with specific status codes
from fastapi.responses import JSONResponse, PlainTextResponse
# Stack trace utilities for detailed error reporting
import traceback
import sys
import os

# Set up enhanced logging
root_logger = logging.getLogger()
if not root_logger.handlers:
    root_logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(handler)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=List[DocumentEmbeddingResponse], status_code=status.HTTP_200_OK)
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
        # Log the upload request with detailed info
        logger.debug(f"Processing upload request for file: {file.filename}")
        
        # Validate file type
        if not file.filename or "." not in file.filename:
            logger.error(f"Invalid file format: {file.filename}")
            return JSONResponse(status_code=400, content={"detail": "Invalid file format"})
            
        # Save and read content
        logger.info(f"Processing file: {file.filename}")
        try:
            filepath = await save_uploaded_document(file)
            logger.debug(f"File saved at: {filepath}")
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            logger.exception("Exception details")
            return JSONResponse(status_code=500, content={"detail": f"Failed to save file: {str(e)}"})
        
        try:
            content = await read_document_content(filepath)
            logger.debug(f"Content extracted, length: {len(content) if content else 0}")
        except Exception as e:
            logger.error(f"Error reading content: {str(e)}")
            logger.exception("Exception details")
            return JSONResponse(status_code=500, content={"detail": f"Failed to read content: {str(e)}"})
        
        if not content or len(content.strip()) == 0:
            logger.error("Document appears to be empty")
            return JSONResponse(status_code=400, content={"detail": "Document appears to be empty"})

        # Chunk + embed
        logger.info(f"Generating chunks and embeddings for {file.filename}")
        try:
            chunks, embeddings, stats = await process_document(content)
            logger.info(f"Successfully generated {len(chunks)} chunks and {len(embeddings)} embeddings")
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            logger.exception("Exception details")
            return JSONResponse(status_code=500, content={"detail": f"Failed to generate embeddings: {str(e)}"})

        # Insert into DB
        responses = []
        try:
            # Batch process all chunks
            for idx, (chunk, embed) in enumerate(zip(chunks, embeddings)):
                try:
                    # Instead of storing the embedding as a JSON string, 
                    # store it as a Python list that SQLAlchemy will convert to a JSON object
                    # This fixes the "column embedding is of type json but expression is of type text" error
                    db_obj = DocumentEmbedding(
                        filename=file.filename,
                        chunk_id=idx,
                        chunk_text=chunk,
                        embedding=embed,  # Direct list object instead of JSON string
                    )
                    db.add(db_obj)
                    responses.append(db_obj)
                except Exception as e:
                    logger.error(f"Error processing chunk {idx}: {str(e)}")
                    continue
            
            # Commit all successful chunks
            try:
                db.commit()
                logger.info(f"Successfully saved {len(responses)} chunks to database")
            except Exception as e:
                logger.error(f"Database commit error: {str(e)}")
                logger.exception("Exception details")
                db.rollback()
                return JSONResponse(status_code=500, content={"detail": f"Database commit error: {str(e)}"})
                
            # Convert to response format
            result = []
            for item in responses:
                result.append({
                    "id": item.id,
                    "filename": item.filename,
                    "chunk_id": item.chunk_id,
                    "chunk_text": item.chunk_text[:100] + "..." if len(item.chunk_text) > 100 else item.chunk_text
                })
                
            return JSONResponse(
                status_code=200,
                content=result
            )
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            logger.exception("Exception details")
            db.rollback()
            return JSONResponse(status_code=500, content={"detail": f"Database error: {str(e)}"})

    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        logger.exception("Exception details")
        try:
            db.rollback()
        except:
            pass
        return JSONResponse(status_code=500, content={"detail": f"Failed to process document: {str(e)}"})