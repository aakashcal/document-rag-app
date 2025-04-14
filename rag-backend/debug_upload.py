import asyncio
import sys
import logging
from fastapi import UploadFile
from app.api.ingestion import upload_document
from app.core.db import SessionLocal
from sqlalchemy.orm import Session
import tempfile
import os

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Get all loggers and set them to DEBUG
loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
for logger in loggers:
    logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

class MockUploadFile(UploadFile):
    """Mock UploadFile for testing without the server"""
    
    def __init__(self, filename, content):
        self.filename = filename
        self._content = content
        self._file = tempfile.NamedTemporaryFile(delete=False)
        with open(self._file.name, 'wb') as f:
            f.write(content)
    
    async def read(self, size=-1):
        with open(self._file.name, 'rb') as f:
            return f.read(size)
    
    def close(self):
        self._file.close()
        try:
            os.unlink(self._file.name)
        except:
            pass

async def test_upload_directly():
    """Test the upload_document function directly with detailed logging"""
    logger.info("Starting direct upload test")
    
    # Prepare test data
    test_file_path = "test.txt"
    try:
        with open(test_file_path, 'rb') as f:
            test_content = f.read()
            
        logger.info(f"Loaded test file: {test_file_path}, size: {len(test_content)} bytes")
        
        # Create mock upload file
        upload_file = MockUploadFile(filename=os.path.basename(test_file_path), content=test_content)
        logger.info(f"Created mock upload file with name: {upload_file.filename}")
        
        # Create database session
        db = SessionLocal()
        try:
            # Process upload
            logger.info("Calling upload_document function directly")
            try:
                result = await upload_document(file=upload_file, db=db)
                logger.info(f"Upload successful with {len(result)} chunks created")
            except Exception as e:
                logger.error(f"Upload function raised exception: {str(e)}", exc_info=True)
                raise
        finally:
            db.close()
            upload_file.close()
            
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        return False
        
    return True

# Run the test
if __name__ == "__main__":
    success = asyncio.run(test_upload_directly())
    logger.info(f"Test result: {'Success' if success else 'Failure'}") 