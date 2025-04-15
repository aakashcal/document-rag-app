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
│   └── DocumentSelector.tsx  # Multi-document selection component
├── App.tsx                   # Main application component and layout
├── main.tsx                  # Application entry point
├── QAInterface.tsx           # Question and answer interface component
├── App.css                   # Application styles (default Vite template)
├── index.css                 # Global styles
└── assets/                   # Static assets
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

## Deployment Details

### Frontend Deployment

The React frontend is deployed using Firebase Hosting's free tier, which provides:
- Global CDN delivery
- Automatic SSL certificates
- Fast response times
- Custom domain support
- Free hosting for small to medium-sized applications

Deployment steps:
1. Install Firebase CLI: `npm install -g firebase-tools`
2. Login to Firebase: `firebase login`
3. Initialize project: `firebase init hosting`
4. Build the application: `npm run build`
5. Deploy to Firebase: `firebase deploy`

### Backend Integration

For a complete deployment, the backend components require:
- PostgreSQL database with pgvector extension (can be hosted on CloudSQL, AWS RDS, or similar)
- Object storage for uploaded documents (Google Cloud Storage, AWS S3, etc.)
- Compute resources for the FastAPI backend (Cloud Run, App Engine, ECS, etc.)

The backend and frontend communicate through API endpoints, with the frontend making requests to the deployed backend services. For local development, both services can run independently with the frontend configured to call the local backend API.
