# Document RAG Application

This repository contains a Retrieval Augmented Generation (RAG) application for document processing, embedding generation, and question answering.

## Project Structure

The application consists of:

1. **Backend (Python/FastAPI)**: A FastAPI application that handles document ingestion, embedding generation, and RAG-based question answering.

## Backend Features

- **Document Ingestion**: Upload documents and generate embeddings
- **Question Answering**: Ask questions about ingested documents using RAG
- **Document Selection**: Specify which documents to consider for Q&A

## Technology Stack

- **Backend**: Python, FastAPI, SQLAlchemy, OpenAI API
- **Database**: PostgreSQL
- **Libraries**: NumPy, tiktoken, python-dotenv

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd document-rag-app
   ```

2. Set up the Python environment:
   ```bash
   cd rag-backend
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the `rag-backend` directory with the following variables:
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

4. Create a PostgreSQL database:
   ```sql
   CREATE DATABASE rag_db;
   ```

### Running the Application

Start the backend server:
```bash
cd rag-backend
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
API documentation is available at `http://localhost:8000/docs`.

## API Endpoints

### Document Management

- `POST /api/documents/`: Ingest a document with JSON payload
- `POST /api/documents/upload`: Upload a document file
- `GET /api/documents/`: Get all documents
- `GET /api/documents/{document_id}`: Get a specific document
- `DELETE /api/documents/{document_id}`: Delete a document

### Question Answering

- `POST /api/qa/`: Ask a question using RAG

### Document Selection

- `POST /api/document-selection/validate`: Validate document selection

## Development

The application is structured as follows:

```
rag-backend/
├── app/
│   ├── api/
│   │   ├── document_select.py
│   │   ├── ingestion.py
│   │   └── qna.py
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
├── uploads/
└── requirements.txt
```

## License

This project is licensed under the MIT License. 