# Document RAG System - Backend

This backend service, built with FastAPI, handles the core logic for the Document Retrieval-Augmented Generation (RAG) system.

## Core Functions

*   **Document Ingestion:** Uploads documents (PDF, TXT), extracts text, splits it into manageable chunks, and generates vector embeddings using OpenAI.
*   **Storage:** Stores document chunks and their embeddings in a PostgreSQL database.
*   **Querying:** Receives user queries, finds the most relevant document chunks using vector similarity search, and uses OpenAI's models to generate an answer based on the retrieved context.
*   **Management:** Allows listing and deleting uploaded documents.

## Folder Structure

```
rag-backend/
├── app/                      # Main application source code
│   ├── api/                  # Defines API endpoints (ingestion, query, document listing/deletion)
│   ├── core/                 # Core components (DB setup, embedding logic)
│   ├── models/               # Data validation schemas (Pydantic models)
│   ├── services/             # Helper services (file storage interaction)
│   ├── config.py             # Handles configuration loading (e.g., from .env)
│   └── main.py               # FastAPI app creation and router inclusion
├── uploads/                  # Default directory for locally uploaded files (if not using cloud storage)
├── .env                      # Local environment variables (API keys, DB connection - **Create from .env.example**)
├── .env.example              # Template for environment variables
├── Dockerfile                # Instructions for building the Docker container image
├── init_db.py                # Script to initialize the database tables
├── requirements.txt          # Python package dependencies
└── README.md                 # This file
```

## Quick Start (Local Development)

1.  **Environment:** Ensure you have Python 3.11+ and a running PostgreSQL server.
2.  **Configure:** Copy `.env.example` to `.env` and fill in your OpenAI API key and PostgreSQL connection details.
3.  **Install:** Set up a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
4.  **Database:** Initialize the database schema. This step also ensures the `vector` extension is enabled in PostgreSQL, which is required for vector similarity operations.
    ```bash
    python init_db.py
    ```
5.  **Run:** Start the development server:
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```

## Vector Storage (PostgreSQL)

*   **Database Extension:** The `init_db.py` script automatically enables the `vector` extension in your PostgreSQL database. This extension provides functions and operators for efficient vector similarity search.
*   **Python Library:** This project uses the `pgvector` library (added to `requirements.txt`) to integrate vector operations with SQLAlchemy.
*   **Embedding Column:** The `embedding` column in the `document_embeddings` table (`app/core/db.py`) is defined using `Vector(1536)` from `pgvector.sqlalchemy`, ensuring embeddings are stored in the native, optimized vector format.
*   **Querying:** Similarity search (`app/api/query.py`) currently loads embeddings from the `Vector` column into NumPy arrays and performs cosine similarity calculations within the Python application using `scikit-learn`. 
*   **Future Enhancement (Optional):** For potentially improved performance on very large datasets, you could update the query logic in `app/api/query.py` to use `pgvector`'s built-in distance operators (like `<->` for cosine distance) directly within the SQL query. This would leverage the database's optimized vector search capabilities, especially if combined with a vector index (e.g., HNSW or IVFFlat) on the embedding column.

## API Endpoints

*   `POST /api/documents/upload`: Upload a document.
*   `POST /api/query/search`: Ask a question based on uploaded documents.
*   `GET /api/documents/list`: List uploaded documents.
*   `DELETE /api/documents/{filename}`: Delete a document.

Access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs` when the server is running.

## Key Technologies

*   FastAPI
*   PostgreSQL with SQLAlchemy
*   OpenAI API (Embeddings & Chat Completion)
*   Docker

## Optional: Cloud Deployment

This application is containerized using Docker (`Dockerfile`) and can be adapted for deployment on cloud platforms like Google Cloud Run, AWS ECS, or Azure Container Apps. This typically involves setting up a managed database (like Cloud SQL or RDS), potentially using cloud storage (like GCS or S3) instead of the local `uploads/` directory, and managing secrets securely.