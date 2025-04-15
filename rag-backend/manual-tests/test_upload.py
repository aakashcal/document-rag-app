import requests
import os
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Test file path - update this to a valid test file
TEST_FILE_PATH = "test.txt"  # Sample file in the repository root

# Upload API endpoint
UPLOAD_URL = "http://127.0.0.1:8004/api/documents/upload"

def test_upload():
    """Test the document upload endpoint with detailed error handling"""
    try:
        logger.info(f"Testing upload with file: {TEST_FILE_PATH}")
        
        # Verify file exists
        if not os.path.exists(TEST_FILE_PATH):
            logger.error(f"Test file does not exist: {TEST_FILE_PATH}")
            return
        
        logger.info(f"File size: {os.path.getsize(TEST_FILE_PATH)} bytes")
        
        # Prepare multipart/form-data
        files = {
            'file': (os.path.basename(TEST_FILE_PATH), open(TEST_FILE_PATH, 'rb'))
        }
        
        # Make the upload request with detailed debugging
        logger.info(f"Sending POST request to {UPLOAD_URL}")
        response = requests.post(
            UPLOAD_URL, 
            files=files,
            timeout=30
        )
        
        # Log response details
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        # Handle different response types
        if response.status_code == 200:
            logger.info("Upload successful")
            result = response.json()
            logger.info(f"Chunks created: {len(result)}")
            return True
        else:
            try:
                error_detail = response.json()
                logger.error(f"Upload failed with error: {error_detail}")
            except:
                logger.error(f"Upload failed with status code {response.status_code}")
                logger.error(f"Response text: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}", exc_info=True)
        return False
    finally:
        # Clean up
        try:
            files['file'][1].close()
        except:
            pass

if __name__ == "__main__":
    # Run test
    success = test_upload()
    logger.info(f"Test result: {'Success' if success else 'Failure'}") 