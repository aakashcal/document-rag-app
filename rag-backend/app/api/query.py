from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session
from app.core.db import get_db, DocumentEmbedding
from app.core.embeddings import prepare_chunks_for_embedding, generate_embeddings
from app.models.schemas import SearchResult
from typing import List, Dict, Any, Optional
import json
import numpy as np
from app.config import settings
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity

router = APIRouter(prefix="/query", tags=["query"])

# Initialize OpenAI client (new style)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# @router.get("/search", response_model=Dict[str, Any])
# async def query_documents_get(
#     q: str = Query(..., description="Your search query"),
#     k: int = Query(5, description="Top k most relevant results"),
#     db: Session = Depends(get_db)
# ):
#     """
#     GET version: Takes a user query, finds top-k relevant document chunks using cosine similarity,
#     and generates a final answer using OpenAI's ChatCompletion API.
#     """
#     return await _process_query(q, k, db)

@router.post("/search", response_model=Dict[str, Any])
async def query_documents_post(
    q: str = Body(..., embed=True, description="Your search query"),
    k: int = Body(5, embed=True, description="Top k most relevant results"),
    document_ids: Optional[List[str]] = Body(None, embed=True, description="Optional list of document IDs to filter results"),
    include_chunks: bool = Body(True, embed=True, description="Whether to include chunks in response"),
    db: Session = Depends(get_db)
):
    """
    POST version: Takes a user query, finds top-k relevant document chunks using cosine similarity,
    and generates a final answer using OpenAI's ChatCompletion API.
    
    Optionally filter by document_ids to search within specific documents.
    """
    return await _process_query(q, k, db, document_ids, include_chunks)

async def _process_query(q: str, k: int, db: Session, document_ids: List[str] = None, include_chunks: bool = True):
    """
    Shared implementation for both GET and POST endpoints
    """
    try:
        # INFO: Received query: {q}
        if document_ids:
            # INFO: Filtering by documents: {document_ids}
            pass

        # 1. Embed the query
        embedding_chunks = prepare_chunks_for_embedding([q], model=settings.OPENAI_EMBEDDING_MODEL)
        query_embedding = await generate_embeddings(embedding_chunks, model=settings.OPENAI_EMBEDDING_MODEL)
        query_vec = np.array(query_embedding[0])

        # 2. Fetch document embeddings, filtered by document_ids if provided
        query = db.query(DocumentEmbedding)
        if document_ids and len(document_ids) > 0:
            # INFO: Filtering search to only include these documents: {document_ids}
            query = query.filter(DocumentEmbedding.filename.in_(document_ids))
            all_docs = query.all()  # No limit when specific documents are selected
        else:
            # Only apply limit when no specific documents are selected
            # INFO: No specific documents selected, using top 500 documents
            all_docs = query.limit(500).all()
            
        if not all_docs:
            raise HTTPException(status_code=404, detail="No document embeddings found with the given criteria")

        # 3. Compare with cosine similarity using sklearn - OPTIMIZED BATCH VERSION
        results = []
        skipped_count = 0
        
        # Get query embedding dimension to use for compatibility check
        query_dim = len(query_vec)
        
        # Prepare for batch processing
        valid_docs = []
        valid_embeddings = []
        
        # First pass: collect compatible embeddings (with early termination)
        max_valid_docs = min(k * 5, 100)  # Get enough valid docs but not too many
        for doc in all_docs:
            # Early termination once we have enough candidates
            if len(valid_docs) >= max_valid_docs:
                # INFO: Early termination at {max_valid_docs} valid docs
                break
                
            try:
                # Parse the embedding
                doc_vec_json = json.loads(doc.embedding)
                doc_vec = np.array(doc_vec_json)
                
                # Check for dimension compatibility
                if len(doc_vec) != query_dim:
                    skipped_count += 1
                    continue
                    
                # Store compatible embeddings and documents
                valid_docs.append(doc)
                valid_embeddings.append(doc_vec)
                
            except Exception as e:
                # WARNING: Failed to process chunk ID {doc.chunk_id}: {e}
                continue
        
        # If we have valid embeddings, calculate similarity in one batch operation
        if valid_embeddings:
            # Stack all embeddings into a single matrix
            embeddings_matrix = np.vstack(valid_embeddings)
            
            # Calculate similarity scores for all docs in one operation (much faster!)
            similarity_scores = sklearn_cosine_similarity([query_vec], embeddings_matrix)[0]
            
            # Create tuples of (score, doc) for each result
            results = [(float(score), doc) for score, doc in zip(similarity_scores, valid_docs)]
        
        # If we've processed everything but have no valid comparisons, return early with a message
        if len(results) == 0:
            # NOTE: Keep the dimension mismatch message if skipped_count > 0
            if skipped_count > 0:
                # WARNING: All {skipped_count} document chunks were skipped due to embedding dimension mismatch
                return {
                    "answer": "I couldn't generate an answer based on the selected documents. There appears to be an embedding dimension mismatch between your query and the documents.",
                    "chunks": []
                }
            else:
                raise HTTPException(status_code=404, detail="No compatible document embeddings found")

        # 4. Sort and keep top-k (Original simple logic)
        results.sort(key=lambda x: x[0], reverse=True)
        top_results = results[:k]

        # 5. Structure response chunks (Original simple logic)
        top_chunks = [
            SearchResult(
                id=doc.id,
                filename=doc.filename,
                chunk_id=doc.chunk_id,
                chunk_text=doc.chunk_text,
                score=round(score, 4),
            )
            for score, doc in top_results
        ]

        # 6. Build context and call LLM for final answer (Original simple logic)
        context_text = "\n\n".join([doc.chunk_text for _, doc in top_results])
        prompt = f"Answer the following question based on the context below:\n\nContext:\n{context_text}\n\nQuestion:\n{q}"

        try:
            # Restore original LLM settings
            chat_response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    # Restore original system message
                    {"role": "system", "content": "You are a helpful assistant that provides concise, accurate answers based on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2, # Original value
                max_tokens=300,  # Original value
                timeout=15.0,    # Original value
                top_p=0.9        # Original value
            )
            answer = chat_response.choices[0].message.content.strip()
            # INFO: Generated answer successfully.
        except Exception as e:
            # ERROR: LLM API call failed: {e}
            answer = "I found relevant information but couldn't generate a complete answer. Try asking a more specific question."

        # 7. Return answer and chunks (Original simple logic)
        response = {"answer": answer}
        if include_chunks:
            response["chunks"] = [chunk.dict() for chunk in top_chunks] # Use top_chunks
        return response

    except Exception as e:
        # ERROR: Search + answer failed: {e}
        raise HTTPException(status_code=500, detail=f"Search + answer failed: {str(e)}")
