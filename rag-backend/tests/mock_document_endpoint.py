from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.core.db import get_db, DocumentEmbedding
from typing import List
from pydantic import BaseModel
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define response model for document list
class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_time: str
    
    class Config:
        from_attributes = True

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/list", response_model=List[DocumentInfo])
async def mock_list_documents(db: Session = Depends(get_db)):
    """
    Mock implementation of the list_documents endpoint for testing with SQLite.
    This version is simplified to work with SQLite's more limited SQL functionality.
    """
    try:
        logger.info("Processing mock request to list all documents")
        
        # Get all document records
        doc_records = db.query(DocumentEmbedding).all()
        
        # Process the results to get unique filenames with earliest upload time
        unique_docs = {}
        for doc in doc_records:
            if doc.filename not in unique_docs or doc.created_at < unique_docs[doc.filename]["time"]:
                unique_docs[doc.filename] = {
                    "id": doc.filename,
                    "filename": doc.filename,
                    "time": doc.created_at,
                }
        
        # Format the response
        document_list = [
            {
                "id": doc_info["id"],
                "filename": doc_info["filename"],
                "upload_time": doc_info["time"].isoformat()
            }
            for doc_info in unique_docs.values()
        ]
        
        logger.info(f"Successfully formatted {len(document_list)} documents for mock response")
        return document_list
    
    except Exception as e:
        logger.error(f"Error in mock list_documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.delete("/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def mock_delete_document(filename: str, db: Session = Depends(get_db)):
    """
    Mock implementation of the delete_document endpoint for testing.
    """
    try:
        logger.info(f"Mock processing request to delete document: '{filename}'")
        
        # Find and delete all chunks for the given filename
        docs_to_delete = db.query(DocumentEmbedding).filter(DocumentEmbedding.filename == filename).all()
        
        if not docs_to_delete:
            logger.warning(f"Attempted to delete non-existent document: {filename}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{filename}' not found.")
            
        # Delete each document
        for doc in docs_to_delete:
            db.delete(doc)
            
        db.commit()
        logger.info(f"Successfully deleted document '{filename}' ({len(docs_to_delete)} chunks)")
        
        return None
    
    except HTTPException as http_exc:
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        logger.error(f"Error in mock delete_document: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"Failed to delete document '{filename}': {str(e)}") 