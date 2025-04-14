from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from fastapi.responses import JSONResponse
import logging
import traceback
import os

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter(prefix="/simple", tags=["simple"])

@router.post("/upload")
async def simple_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Simplified upload endpoint for debugging the 500 Internal Server Error
    """
    try:
        logger.debug(f"Processing upload request for file: {file.filename}")
        
        # Validation
        if not file.filename:
            return JSONResponse(status_code=400, content={"detail": "No filename provided"})
        
        # Just save the file without further processing
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        try:
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
                
            return JSONResponse(
                status_code=200, 
                content={
                    "filename": file.filename, 
                    "size": len(content),
                    "saved_path": file_path
                }
            )
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=500, 
                content={"detail": f"File save error: {str(e)}", "traceback": traceback.format_exc()}
            )
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500, 
            content={"detail": f"Unexpected error: {str(e)}", "traceback": traceback.format_exc()}
        ) 