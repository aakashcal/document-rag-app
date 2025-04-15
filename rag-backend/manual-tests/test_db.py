from sqlalchemy import text
from app.core.db import engine, get_db, SessionLocal

print("Testing database connection...")
try:
    # Test connection with raw query
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(f"Database connection successful: {result.scalar()}")
        
    # Test session creation
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT current_database()")).scalar()
        print(f"Connected to database: {result}")
    finally:
        db.close()
except Exception as e:
    print(f"Database error: {str(e)}") 