"""
Database initialization script.

This script initializes the PostgreSQL database with the required schema and extensions.
Run this script before starting the application to ensure the database is properly set up.
"""

from app.core.db import init_db
# import logging # Removed

# Configure logging
# logging.basicConfig( # Removed
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__) # Removed

if __name__ == "__main__":
    # logger.info("Initializing database...") # Replaced
    # INFO: Initializing database...
    try:
        init_db()
        # logger.info("Database initialization completed successfully.") # Replaced
        # INFO: Database initialization completed successfully.
    except Exception as e:
        # logger.error(f"Database initialization failed: {str(e)}", exc_info=True) # Replaced
        # ERROR: Database initialization failed: {str(e)} # Add exc_info=True if needed for debugging
        raise 