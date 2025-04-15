import requests
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# API endpoints to test
ENDPOINTS = [
    "http://127.0.0.1:8004/api/documents/list",  # List documents endpoint
]

def test_api_endpoints():
    """Test the API endpoints to verify they're working"""
    results = {}
    
    for endpoint in ENDPOINTS:
        try:
            logger.info(f"Testing endpoint: {endpoint}")
            response = requests.get(endpoint, timeout=10)
            
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response headers: {response.headers}")
            
            # Try to parse response
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"Response data: {data}")
                    results[endpoint] = True
                except Exception as parse_error:
                    logger.error(f"Failed to parse JSON response: {str(parse_error)}")
                    logger.error(f"Response text: {response.text[:200]}...")
                    results[endpoint] = False
            else:
                logger.error(f"Request failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text[:200]}...")
                results[endpoint] = False
        except Exception as e:
            logger.error(f"Request failed with exception: {str(e)}", exc_info=True)
            results[endpoint] = False
    
    return results

if __name__ == "__main__":
    results = test_api_endpoints()
    success = all(results.values())
    logger.info(f"Overall test result: {'Success' if success else 'Failure'}")
    
    # Print summary
    for endpoint, result in results.items():
        logger.info(f"{endpoint}: {'Success' if result else 'Failure'}") 