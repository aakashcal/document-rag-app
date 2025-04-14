from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import distinct, func
from app.core.db import get_db, DocumentEmbedding
from typing import List
from pydantic import BaseModel
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define response model for document list
class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_time: str
    
    class Config:
        from_attributes = True

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/list", 
            response_model=List[DocumentInfo],
            responses={
                200: {"description": "Successfully retrieved the list of documents."},
                500: {"description": "Internal server error while retrieving documents."}
            })
async def list_documents(db: Session = Depends(get_db)):
    """
    List all unique documents available in the system.
    
    Returns a list of documents with their filenames and upload times.
    Each document appears only once, even if it has multiple chunks.
    """
    try:
        logger.info("Processing request to list all documents")
        
        # Query to get unique filenames with their earliest upload time
        # This ensures we get one entry per document
        try:
            query = (
                db.query(
                    DocumentEmbedding.filename.label("filename"),
                    func.min(DocumentEmbedding.created_at).label("upload_time")
                )
                .group_by(DocumentEmbedding.filename)
                .order_by(func.min(DocumentEmbedding.created_at).desc())
            )
            
            results = query.all()
            logger.debug(f"Retrieved {len(results)} unique documents from database")
        except Exception as query_error:
            logger.error(f"Database error retrieving document list: {str(query_error)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Failed to query documents: {str(query_error)}")
        
        # Format the results for the API response
        document_list = []
        for result in results:
            # Use filename as ID (can be enhanced with a proper UUID if needed)
            document_list.append({
                "id": result.filename,
                "filename": result.filename,
                "upload_time": result.upload_time.isoformat()
            })
        
        logger.info(f"Successfully formatted {len(document_list)} documents for response")
        return document_list
    
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@router.delete("/{filename}", 
               status_code=status.HTTP_204_NO_CONTENT,
               responses={
                   204: {"description": "Document deleted successfully. No content returned."},
                   404: {"description": "Document with the specified filename not found."},
                   500: {"description": "Internal server error while deleting the document."}
               })
async def delete_document(filename: str, db: Session = Depends(get_db)):
    """
    Delete a document and all its associated embedding chunks from the database.
    """
    try:
        logger.info(f"Processing request to delete document: '{filename}'")
        
        # Find all chunks associated with the filename
        try:
            chunks_to_delete = db.query(DocumentEmbedding).filter(DocumentEmbedding.filename == filename).all()
            logger.debug(f"Found {len(chunks_to_delete)} chunks to delete for document '{filename}'")

            if not chunks_to_delete:
                logger.warning(f"Attempted to delete non-existent document: {filename}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document '{filename}' not found.")
        except Exception as find_error:
            if isinstance(find_error, HTTPException):
                raise
            logger.error(f"Error finding chunks to delete: {str(find_error)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Failed to find document chunks: {str(find_error)}")

        try:
            # Delete the found chunks
            num_deleted = db.query(DocumentEmbedding).filter(DocumentEmbedding.filename == filename).delete()
            db.commit()
            logger.info(f"Successfully deleted document '{filename}' ({num_deleted} chunks)")
        except Exception as delete_error:
            db.rollback()
            logger.error(f"Error deleting document chunks: {str(delete_error)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Failed to delete document chunks: {str(delete_error)}")

        # Return No Content response
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except HTTPException as http_exc:
        # Re-raise HTTP exceptions directly
        db.rollback()
        raise http_exc
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting document '{filename}': {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete document '{filename}': {str(e)}")
