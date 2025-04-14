from app.core.db import SessionLocal, DocumentEmbedding, Base, engine
from sqlalchemy import inspect

print("Testing database table structure...")
try:
    # Create an inspector
    inspector = inspect(engine)
    
    # Check if our table exists
    table_exists = inspector.has_table("document_embeddings")
    print(f"Table 'document_embeddings' exists: {table_exists}")
    
    if table_exists:
        # Get table columns
        columns = inspector.get_columns("document_embeddings")
        print(f"Columns in table: {[col['name'] for col in columns]}")
        
        # Count records
        session = SessionLocal()
        try:
            record_count = session.query(DocumentEmbedding).count()
            print(f"Number of records in table: {record_count}")
        finally:
            session.close()
    else:
        print("Creating table schema...")
        Base.metadata.create_all(bind=engine)
        print("Table schema created.")
except Exception as e:
    print(f"Error: {str(e)}") 