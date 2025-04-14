# Document RAG Application - Frontend

A React frontend for the Document RAG system that provides a user interface for uploading documents, asking questions, and viewing AI-generated answers.

## Features

* Upload documents (PDF, TXT)
* Select documents to use for question answering
* Ask questions about your documents
* View AI-generated answers with source references
* Delete documents

## Component Structure

```
src/
├── components/
│   ├── DocumentUpload.tsx    # Document upload component
│   ├── DocumentSelector.tsx  # Multi-document selection component
│   ├── QuestionInput.tsx     # Question input and submission form
│   ├── AnswerDisplay.tsx     # Displays AI-generated answers with formatting
│   └── DocumentList.tsx      # List of documents with delete functionality
├── App.tsx                   # Main application component and layout
├── main.tsx                  # Application entry point
└── api/
    └── apiClient.ts          # API communication functions
```

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Run development server:**
   ```bash
   npm run dev
   ```

3. **Access the app:**
   Open http://localhost:5173 in your browser

## Building for Production

```bash
npm run build
```

## Technology Stack

* React + TypeScript
* Material UI
* TanStack Query
* Vite

## Deployment

This frontend is deployed at: https://document-rag-app-381fb.web.app
