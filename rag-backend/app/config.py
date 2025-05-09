"""
Configuration for the RAG application.
Loads settings from environment variables with defaults.
Required for OpenAI API and database connections.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """
    Application configuration with environment variable support.
    Provides OpenAI API settings and database connection parameters.
   
     OpenAI settings:
        - OPENAI_API_KEY: Required API key for OpenAI services
        - OPENAI_EMBEDDING_MODEL: Model used for generating text embeddings
        - OPENAI_COMPLETION_MODEL: Model used for generating text completions
        
     Database settings:
        - DB_HOST: Database server hostname/IP
        - DB_PORT: Database server port
        - DB_NAME: Database name for the application
        - DB_USER: Database username
        - DB_PASSWORD: Database password
    
    """
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_COMPLETION_MODEL: str = "gpt-3.5-turbo"
    
    # Embedding processing configuration
    CHUNK_SIZE: int = 1000  # Default chunk size in tokens
    CHUNK_OVERLAP: int = 200  # Default overlap between chunks in tokens
    EMBEDDING_BATCH_SIZE: int = 20  # Default batch size for embedding API calls

    # Database configuration from environment variables with defaults
    # Only non-sensitive defaults are provided here
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "document-rag-app")
    DB_USER: str = os.getenv("DB_USER", "")  # No default for security
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")  # No default for security

    # Updated Config for Pydantic V2
    model_config = SettingsConfigDict(env_file=".env")

# Load settings from environment
settings = Settings()