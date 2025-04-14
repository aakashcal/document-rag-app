# Document RAG Application - Backend

This repository contains the backend component of a Retrieval Augmented Generation (RAG) application for document processing, embedding generation, and question answering.

## Features

* **Document Ingestion:** Upload documents and generate embeddings
* **Question Answering:** Ask questions about ingested documents using RAG
* **Document Selection:** Specify which documents to consider for Q&A
* **Vector Storage:** Efficiently store and retrieve document embeddings using PostgreSQL

## RAG Implementation Details

The application implements a complete Retrieval Augmented Generation pipeline:

### Document Processing Flow
1. **Document Ingestion**: 
   - Documents are uploaded through the API
   - Text is extracted from various formats (PDF, TXT, etc.)
   - The text is split into smaller chunks (typically paragraphs or sections)
   - Each chunk is processed to remove unnecessary whitespace and formatting

2. **Embedding Generation**:
   - Each text chunk is converted into a vector embedding using OpenAI's embedding model
   - These high-dimensional vectors capture the semantic meaning of each text segment
   - Embeddings are stored in PostgreSQL using the pgvector extension, which allows for efficient vector similarity search

3. **Document Management**:
   - Metadata about the document (filename, upload date, etc.) is stored alongside the chunks
   - Documents can be selected or deselected for inclusion in the search context

### Query Processing Flow
1. **Query Embedding**:
   - User questions are embedded using the same OpenAI embedding model
   - This produces a vector representation semantically similar to the query

2. **Semantic Retrieval**:
   - The system performs a similarity search between the query embedding and all stored document chunk embeddings
   - The most semantically relevant chunks are retrieved based on cosine similarity scores
   - A configurable number of chunks is selected to form the context for the LLM

3. **Context Assembly**:
   - Retrieved chunks are assembled into a prompt context
   - Document sources are tracked to provide attribution in responses

4. **Answer Generation**:
   - The assembled context and original question are sent to OpenAI's completion model
   - The model generates a comprehensive answer based only on the provided context
   - Responses include citations to source documents when appropriate

This implementation ensures that answers are:
* Grounded in your specific documents
* Up-to-date with your latest information
* Traceable to source materials
* More accurate than generic LLM responses

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
│   │   └── query.py
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
* `POST /api/documents/upload`: Upload a document file
* `GET /api/documents/list`: List all documents
* `DELETE /api/documents/{filename}`: Delete a document by filename

### Question Answering
* `POST /api/query/search`: Ask a question about documents using RAG (accepts optional `document_ids` parameter to filter which documents to search)

## Vector Storage (PostgreSQL)

* **Database Extension:** The application uses the `vector` extension in PostgreSQL for efficient vector similarity search.
* **Python Library:** The project uses the `pgvector` library to integrate vector operations with SQLAlchemy.
* **Embedding Column:** Embeddings are stored in the native, optimized vector format using `Vector(1536)` from `pgvector.sqlalchemy`.

## Deployment

This application is containerized using Docker and can be deployed on cloud platforms like Google Cloud Run, AWS ECS, or Azure Container Apps.

## License

This project is licensed under the MIT License.