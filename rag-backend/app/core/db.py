"""
Database connection setup module for the RAG application.

This module establishes the SQLAlchemy connection to PostgreSQL database and
provides utilities for database session management through a dependency
injection pattern optimized for FastAPI.
"""

from sqlalchemy import create_engine, pool, Column, Integer, String, Text, DateTime, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSON
from app.config import settings
import urllib.parse
import os

# URL-encode password to handle special characters
encoded_password = urllib.parse.quote_plus(settings.DB_PASSWORD)

# Determine DB Host: Use host.docker.internal if running in Docker, else use .env value
db_host = 'host.docker.internal' if os.environ.get('RUNNING_IN_DOCKER') == 'true' else settings.DB_HOST

# Construct PostgreSQL connection string from configuration
DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:{encoded_password}"
    f"@{db_host}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Initialize database engine with the connection string and connection pooling optimizations
# Connection pooling reduces overhead by reusing database connections instead of creating new ones for each request
engine = create_engine(
    DATABASE_URL,
    pool_size=5,                  # Number of connections to keep open
    max_overflow=10,              # Max extra connections to create
    pool_timeout=30,              # Seconds to wait before timeout
    pool_recycle=1800,            # Recycle connections after 30 min
    pool_pre_ping=True            # Verify connection is still alive before using
)

# Create session factory configured for this application's needs
# - autocommit=False: Transactions must be explicitly committed
# - autoflush=False: Changes won't be flushed to DB automatically before queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
# All ORM models will inherit from this base
Base = declarative_base()

# FastAPI dependency for database session management
def get_db():
    """
    Dependency provider that yields a database session.
    
    Creates a new SQLAlchemy session for each request and automatically
    closes it when the request is complete, ensuring proper resource cleanup.
    
    Usage in FastAPI route:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    # Create new session for this request
    db = SessionLocal()
    try:
        # Yield session to the route function
        yield db
    finally:
        # Ensure session is closed even if an exception occurs
        db.close()

class DocumentEmbedding(Base):
    """
    Database model for document embeddings.
    
    Stores text chunks from documents along with their vector embeddings
    for retrieval during RAG operations.
    """
    __tablename__ = "document_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    chunk_id = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    # For pgvector compatibility, we store embedding as JSON in text column
    # When used with pgvector, this will be cast to vector type during queries
    # The format must be a proper JSON array: [0.1, 0.2, ...]
    embedding = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Create database tables
def init_db():
    """Initialize database with required extensions and tables."""
    with engine.connect() as conn:
        # Check if vector extension exists
        result = conn.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');"))
        has_vector = result.scalar()
        
        if not has_vector:
            # Create vector extension if it doesn't exist
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            
        # Create tables
        Base.metadata.create_all(bind=engine)
        
    return True