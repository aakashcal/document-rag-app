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
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    logger.debug(f"Received search request: query='{q}', k={k}, document_ids={document_ids}, include_chunks={include_chunks}")
    return await _process_query(q, k, db, document_ids, include_chunks)

async def _process_query(q: str, k: int, db: Session, document_ids: List[str] = None, include_chunks: bool = True):
    """
    Shared implementation for both GET and POST endpoints
    """
    try:
        # Log the received query
        logger.info(f"Processing query: {q}")
        
        # Log if we're filtering by specific documents
        if document_ids:
            logger.info(f"Filtering by documents: {document_ids}")

        # 1. Embed the query
        logger.debug("Generating embedding for query")
        try:
            embedding_chunks = prepare_chunks_for_embedding([q], model=settings.OPENAI_EMBEDDING_MODEL)
            query_embedding = await generate_embeddings(embedding_chunks, model=settings.OPENAI_EMBEDDING_MODEL)
            query_vec = np.array(query_embedding[0])
            logger.debug(f"Query embedding generated successfully: {len(query_vec)} dimensions")
        except Exception as embed_error:
            logger.error(f"Error generating query embedding: {str(embed_error)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Failed to generate query embedding: {str(embed_error)}")

        # 2. Fetch document embeddings, filtered by document_ids if provided
        try:
            query = db.query(DocumentEmbedding)
            if document_ids and len(document_ids) > 0:
                logger.info(f"Filtering search to only include these documents: {document_ids}")
                query = query.filter(DocumentEmbedding.filename.in_(document_ids))
                all_docs = query.all()  # No limit when specific documents are selected
                logger.debug(f"Retrieved {len(all_docs)} document chunks for specified documents")
            else:
                # Only apply limit when no specific documents are selected
                logger.info("No specific documents selected, using top 500 documents")
                all_docs = query.limit(500).all()
                logger.debug(f"Retrieved {len(all_docs)} document chunks (limit: 500)")
                
            if not all_docs:
                logger.warning("No document embeddings found with the given criteria")
                raise HTTPException(status_code=404, detail="No document embeddings found with the given criteria")
        except Exception as db_error:
            if isinstance(db_error, HTTPException):
                raise
            logger.error(f"Database error fetching document embeddings: {str(db_error)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Failed to fetch document embeddings: {str(db_error)}")

        # 3. Compare with cosine similarity using sklearn - OPTIMIZED BATCH VERSION
        results = []
        skipped_count = 0
        
        # Get query embedding dimension to use for compatibility check
        query_dim = len(query_vec)
        logger.debug(f"Query dimension: {query_dim}")
        
        # Prepare for batch processing
        valid_docs = []
        valid_embeddings = []
        
        # First pass: collect compatible embeddings (with early termination)
        max_valid_docs = min(k * 5, 100)  # Get enough valid docs but not too many
        logger.debug(f"Collecting up to {max_valid_docs} valid documents for similarity comparison")
        
        for doc in all_docs:
            # Early termination once we have enough candidates
            if len(valid_docs) >= max_valid_docs:
                logger.info(f"Early termination at {max_valid_docs} valid docs")
                break
                
            try:
                # Parse the embedding - handle both JSON string and direct list object storage
                if isinstance(doc.embedding, str):
                    # Handle old format (JSON string)
                    doc_vec_json = json.loads(doc.embedding)
                    doc_vec = np.array(doc_vec_json)
                else:
                    # Handle new format (already a list/object)
                    doc_vec = np.array(doc.embedding)
                
                # Check for dimension compatibility
                if len(doc_vec) != query_dim:
                    logger.warning(f"Dimension mismatch for chunk {doc.chunk_id}: expected {query_dim}, got {len(doc_vec)}")
                    skipped_count += 1
                    continue
                    
                # Store compatible embeddings and documents
                valid_docs.append(doc)
                valid_embeddings.append(doc_vec)
                
            except Exception as e:
                logger.warning(f"Failed to process chunk ID {doc.chunk_id}: {e}")
                continue
        
        logger.info(f"Found {len(valid_docs)} compatible documents, skipped {skipped_count} incompatible ones")
        
        # If we have valid embeddings, calculate similarity in one batch operation
        if valid_embeddings:
            # Stack all embeddings into a single matrix
            embeddings_matrix = np.vstack(valid_embeddings)
            
            # Calculate similarity scores for all docs in one operation (much faster!)
            logger.debug("Calculating similarity scores in batch")
            similarity_scores = sklearn_cosine_similarity([query_vec], embeddings_matrix)[0]
            
            # Create tuples of (score, doc) for each result
            results = [(float(score), doc) for score, doc in zip(similarity_scores, valid_docs)]
            logger.debug(f"Generated {len(results)} similarity scores")
        
        # If we've processed everything but have no valid comparisons, return early with a message
        if len(results) == 0:
            # NOTE: Keep the dimension mismatch message if skipped_count > 0
            if skipped_count > 0:
                logger.warning(f"All {skipped_count} document chunks were skipped due to embedding dimension mismatch")
                return {
                    "answer": "I couldn't generate an answer based on the selected documents. There appears to be an embedding dimension mismatch between your query and the documents.",
                    "chunks": []
                }
            else:
                logger.warning("No valid document embeddings found for comparison")
                raise HTTPException(status_code=404, detail="No document embeddings found with the given criteria")

        # 4. Sort and keep top-k (Original simple logic)
        results.sort(key=lambda x: x[0], reverse=True)
        top_results = results[:k]
        logger.info(f"Selected top {len(top_results)} results with scores: {[round(score, 4) for score, _ in top_results]}")

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
        logger.debug(f"Built context with {len(top_results)} chunks, total length: {len(context_text)} characters")

        try:
            logger.info("Calling OpenAI API to generate answer")
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
            logger.info("Generated answer successfully")
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            logger.error(traceback.format_exc())
            answer = "I found relevant information but couldn't generate a complete answer. Try asking a more specific question."

        # 7. Return answer and chunks (Original simple logic)
        response = {"answer": answer}
        if include_chunks:
            response["chunks"] = [chunk.dict() for chunk in top_chunks] # Use top_chunks
            logger.debug(f"Including {len(top_chunks)} chunks in response")
        else:
            logger.debug("Chunks not included in response")
        
        return response

    except Exception as e:
        logger.error(f"Search + answer failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Search + answer failed: {str(e)}")
