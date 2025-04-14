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
4.  **Database:** Initialize the database schema:
    ```bash
    python init_db.py
    ```
5.  **Run:** Start the development server:
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```

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

## Deployment Status & Next Steps (Cloud)

This backend application has been prepared for cloud deployment but requires further steps for a fully functional cloud environment.

*   **Containerization:**
    *   A `Dockerfile` is provided to containerize the application.
    *   The image builds successfully and runs locally using Docker (`docker build -t rag-backend-image .`, `docker run -d -p 8000:8000 --env-file .env --name rag-backend-container rag-backend-image`).
    *   The image has been pushed to Google Cloud Artifact Registry at: `asia-south1-docker.pkg.dev/document-rag-app/rag-app-repo/rag-backend:latest`.
*   **Target Platform:** Google Cloud Run (`asia-south1` region).
*   **Next Steps Required for Cloud Deployment:**
    1.  **Database Setup (Cloud SQL):**
        *   **Why:** Cloud Run requires a network-accessible database. Localhost DB is not reachable. A managed service like Cloud SQL is recommended for persistence and scalability.
        *   **Action:** Create a PostgreSQL instance on Cloud SQL. Configure secure connection from Cloud Run (e.g., using Cloud SQL Auth Proxy/connector). Update `DB_*` environment variables for the Cloud Run service.
    2.  **File Storage (Google Cloud Storage - GCS):**
        *   **Why:** Cloud Run has an ephemeral filesystem. Files uploaded directly to the container will be lost on restarts/deployments. GCS provides persistent object storage.
        *   **Action:** Create a GCS bucket. Modify the `app/services/storage.py` module to use the `google-cloud-storage` client library for uploading to and reading from the GCS bucket instead of the local filesystem. Grant the Cloud Run service account permissions to access the bucket.
    3.  **Secrets Management (Secret Manager):**
        *   **Why:** Avoid passing sensitive data (API keys, DB passwords) directly as environment variables.
        *   **Action:** Store `OPENAI_API_KEY` and `DB_PASSWORD` in Google Cloud Secret Manager. Grant the Cloud Run service account permission to access these secrets. Modify the Cloud Run deployment configuration to mount secrets as environment variables. *(Partially started - Secrets created but not yet integrated into deployment)*.
    4.  **Deploy Service (`gcloud run deploy`):**
        *   **Action:** Use the `gcloud run deploy` command, specifying the Artifact Registry image URL, region, environment variables (pointing to secrets for sensitive values), and Cloud SQL connection details.

## Technology Stack

*   FastAPI
*   Uvicorn
*   SQLAlchemy
*   PostgreSQL
*   Pydantic / Pydantic-Settings
*   OpenAI API Client
*   Tiktoken
*   PyMuPDF
*   Tenacity
*   Scikit-learn
*   Docker