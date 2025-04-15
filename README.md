# Document RAG Application

A Retrieval Augmented Generation (RAG) system that allows users to upload documents, process them into embeddings, and ask natural language questions about their content.

## Project Overview

This application leverages the power of large language models (LLMs) and vector databases to implement a complete RAG pipeline. Users can upload documents, which are processed, chunked, and stored as vector embeddings. When users ask questions, the system retrieves the most relevant document chunks and uses an LLM to generate answers based on the context.

## Application Screenshots

### Backend API
<div align="center">
  <img src="./images/backend.png" alt="FastAPI Backend" width="800"/>
</div>

### Frontend Interface
<div align="center">
  <img src="./images/frontend.png" alt="React Frontend Interface" width="800"/>
</div>


## Project Structure

The application is divided into two main components:

```
document-rag-app/
├── rag-backend/         # FastAPI backend service
│   ├── app/             # Main application code
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core functionality (DB, embeddings)
│   │   ├── models/      # Data models
│   │   └── services/    # Helper services
│   ├── uploads/         # Document storage
│   └── tests/           # Test files
│
└── react-frontend/      # React frontend UI
    ├── src/             # Source code
    │   ├── components/  # React components
    │   └── assets/      # Static assets
    └── public/          # Public files
```

## Additional Documentation

- [Backend Documentation](./rag-backend/README.md)
- [Frontend Documentation](./react-frontend/README.md)

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with pgvector extension for vector search
- **AI/ML**: OpenAI API for embeddings and completions
- **Libraries**: SQLAlchemy, NumPy, tiktoken

### Frontend
- **Framework**: React with TypeScript
- **UI**: Material UI
- **API Integration**: TanStack Query
- **Build Tool**: Vite

## Key Features

1. **Document Management**
   - Upload and process various document formats
   - List and delete documents

2. **Semantic Search**
   - Convert user questions into embeddings
   - Retrieve relevant document chunks using vector similarity

3. **Question Answering**
   - Generate comprehensive answers from document context
   - Provide source references

4. **Document Filtering**
   - Select which documents to include in the search context

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js
- PostgreSQL with vector extension enabled
- OpenAI API key

### Running the Backend
```bash
cd rag-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables in .env file
# Initialize the database
python init_db.py

# Start the server
uvicorn app.main:app --reload
```

### Running the Frontend
```bash
cd react-frontend
npm install
npm run dev
```

Access the application at http://localhost:5173

## Deployment

- **Backend**: Can be deployed as a containerized service using Docker
- **Frontend**: Deployed on Firebase hosting at https://document-rag-app-381fb.web.app

## License

This project is licensed under the MIT License.
