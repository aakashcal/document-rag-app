# Document RAG Application - Backend

This repository contains the backend component of a Retrieval Augmented Generation (RAG) application for document processing, embedding generation, and question answering.

## Features

* **Document Ingestion:** Upload documents and generate embeddings
* **Question Answering:** Ask questions about ingested documents using RAG
* **Document Selection:** Specify which documents to consider for Q&A
* **Vector Storage:** Efficiently store and retrieve document embeddings using PostgreSQL

## Technology Stack

* **Framework:** Python, FastAPI, SQLAlchemy
* **AI Models:** OpenAI API (embeddings and completions)
* **Database:** PostgreSQL with pgvector extension
* **Libraries:** NumPy, tiktoken, python-dotenv

## Folder Structure

```
rag-backend/
├── app/
│   ├── api/
│   │   ├── document_select.py
│   │   ├── ingestion.py
│   │   ├── query.py
│   │   └── simple_upload.py
│   ├── core/
│   │   ├── db.py
│   │   ├── embeddings.py
│   │   └── retrieval.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   └── storage.py
│   ├── config.py
│   └── main.py
├── uploads/               # Default directory for locally uploaded files
├── tests/                 # Test files
├── .env                   # Local environment variables (not committed to git)
├── Dockerfile             # Instructions for building the Docker container image
├── requirements.txt       # Python package dependencies
└── README.md              # This file
```

## Getting Started

### Prerequisites

* Python 3.8+
* PostgreSQL with vector extension
* OpenAI API key

### Installation

1. Set up the Python environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

2. Create a `.env` file in the rag-backend directory with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_COMPLETION_MODEL=gpt-3.5-turbo

DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_db
DB_USER=postgres
DB_PASSWORD=your_db_password
```

3. Initialize the database schema:

```bash
python init_db.py
```

### Running the Application

Start the backend server:

```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000. API documentation is available at http://localhost:8000/docs.

## API Endpoints

### Document Management
* `POST /api/documents/`: Ingest a document with JSON payload
* `POST /api/documents/upload`: Upload a document file
* `GET /api/documents/`: Get all documents
* `GET /api/documents/{document_id}`: Get a specific document
* `DELETE /api/documents/{document_id}`: Delete a document

### Question Answering
* `POST /api/qa/`: Ask a question using RAG

### Document Selection
* `POST /api/document-selection/validate`: Validate document selection

## Vector Storage (PostgreSQL)

* **Database Extension:** The application uses the `vector` extension in PostgreSQL for efficient vector similarity search.
* **Python Library:** The project uses the `pgvector` library to integrate vector operations with SQLAlchemy.
* **Embedding Column:** Embeddings are stored in the native, optimized vector format using `Vector(1536)` from `pgvector.sqlalchemy`.

## Deployment

This application is containerized using Docker and can be deployed on cloud platforms like Google Cloud Run, AWS ECS, or Azure Container Apps.

## License

This project is licensed under the MIT License.