"""
Embeddings module for document processing.

Handles text chunking and embedding generation for the RAG application.
Uses OpenAI API to generate embeddings from text chunks with:
- Token-aware chunking with configurable chunk size and overlap
- Chunk validation with truncation if tokens exceed model limits
- Batch embedding requests for efficiency with configurable batch size
- Retry logic using tenacity with exponential backoff
- Async OpenAI API usage via AsyncOpenAI client
- Raw vector return format for direct use or storage
- Token statistics logging for optimization
"""

import openai
import json
import tiktoken
import time
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings
from typing import List, Tuple, Dict, Any, Optional, Union
# import logging # Removed

# logger = logging.getLogger(__name__) # Removed

# Configure OpenAI API
openai.api_key = settings.OPENAI_API_KEY

# Constants
MAX_TOKENS_PER_CHUNK = 8191  # OpenAI embedding model limit
MAX_RETRIES = 3  # Reduced from 5 for faster failure
MIN_RETRY_SECONDS = 0.5  # Reduced minimum backoff time
MAX_RETRY_SECONDS = 30  # Reduced maximum backoff time

def get_encoding_for_model(model: str) -> tiktoken.Encoding:
    """Get the appropriate encoding for the specified model."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fall back to cl100k_base if specific model encoding not found
        encoding = tiktoken.get_encoding("cl100k_base")
    return encoding

def chunk_text(
    text: str, 
    chunk_size: Optional[int] = None, 
    overlap: Optional[int] = None,
    model: Optional[str] = None
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Split text into chunks with token awareness and overlap.
    
    Args:
        text: The document content to chunk
        chunk_size: Target size of each chunk in tokens (default from settings)
        overlap: Number of overlapping tokens between chunks (default from settings)
        model: The model to use for tokenization (default from settings)
        
    Returns:
        Tuple of (chunks, stats) where stats contains token information
    """
    if not text:
        return [], {"total_tokens": 0, "chunk_count": 0, "avg_chunk_tokens": 0}
    
    # Use defaults from settings if not provided
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP
    model = model or settings.OPENAI_EMBEDDING_MODEL

    # Get tokenizer based on embedding model
    encoding = get_encoding_for_model(model)
    
    # Tokenize the text
    tokens = encoding.encode(text)
    total_tokens = len(tokens)
    
    # Create chunks with overlap
    chunks = []
    chunk_token_counts = []
    i = 0
    while i < total_tokens:
        # Get chunk_size tokens or remaining tokens
        chunk_end = min(i + chunk_size, total_tokens)
        # Decode chunk back to text
        chunk_tokens = tokens[i:chunk_end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        chunk_token_counts.append(len(chunk_tokens))
        
        # Move forward by chunk_size - overlap
        i += (chunk_size - overlap)
        # Ensure we don't get stuck in a loop with very small chunks
        if i >= total_tokens - overlap and i < total_tokens:
            remaining_tokens = tokens[i:]
            chunks.append(encoding.decode(remaining_tokens))
            chunk_token_counts.append(len(remaining_tokens))
            break
    
    # Compute statistics
    stats = {
        "total_tokens": total_tokens,
        "chunk_count": len(chunks),
        "avg_chunk_tokens": sum(chunk_token_counts) / len(chunks) if chunks else 0,
        "min_chunk_tokens": min(chunk_token_counts) if chunks else 0,
        "max_chunk_tokens": max(chunk_token_counts) if chunks else 0,
    }
    
    return chunks, stats

def validate_chunk_length(chunk: str, model: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a chunk isn't too long for the embedding model.
    
    Args:
        chunk: The text chunk to validate
        model: The embedding model being used
        
    Returns:
        (is_valid, truncated_chunk) where truncated_chunk is None if no truncation needed
    """
    encoding = get_encoding_for_model(model)
    tokens = encoding.encode(chunk)
    
    if len(tokens) <= MAX_TOKENS_PER_CHUNK:
        return True, None
    
    # Truncate if too long
    # logger.warning(f"Chunk exceeds token limit ({len(tokens)} > {MAX_TOKENS_PER_CHUNK}). Truncating.") # Replaced
    # WARNING: Chunk exceeds token limit ({len(tokens)} > {MAX_TOKENS_PER_CHUNK}). Truncating.
    truncated_tokens = tokens[:MAX_TOKENS_PER_CHUNK]
    truncated_chunk = encoding.decode(truncated_tokens)
    
    return False, truncated_chunk

def prepare_chunks_for_embedding(chunks: List[str], model: str) -> List[str]:
    """
    Validate and prepare chunks for embedding.
    
    Args:
        chunks: List of text chunks
        model: The embedding model being used
        
    Returns:
        List of validated and possibly truncated chunks
    """
    validated_chunks = []
    
    for chunk in chunks:
        is_valid, truncated_chunk = validate_chunk_length(chunk, model)
        if is_valid:
            validated_chunks.append(chunk)
        elif truncated_chunk is not None:
            validated_chunks.append(truncated_chunk)
    
    return validated_chunks

# Retry decorator for API calls - optimized for faster recovery
@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=0.5, min=MIN_RETRY_SECONDS, max=MAX_RETRY_SECONDS),
    retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)),
    reraise=True
)
async def _create_embeddings_with_retry(client, batch, model):
    """Create embeddings with retry logic."""
    try:
        # Add timeout for faster response in case of API slowness
        return await asyncio.wait_for(
            client.embeddings.create(input=batch, model=model),
            timeout=10.0  # 10 second timeout
        )
    except asyncio.TimeoutError:
        # logger.warning("OpenAI API call timed out after 10 seconds. Retrying...") # Replaced
        # WARNING: OpenAI API call timed out after 10 seconds. Retrying...
        raise openai.APITimeoutError("Request timed out")
    except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as e:
        # logger.warning(f"OpenAI API error: {str(e)}. Retrying...") # Replaced
        # WARNING: OpenAI API error: {str(e)}. Retrying...
        raise
    except Exception as e:
        # logger.error(f"Unexpected error during embedding creation: {str(e)}") # Replaced
        # ERROR: Unexpected error during embedding creation: {str(e)}
        raise

async def generate_embeddings(
    chunks: List[str],
    batch_size: Optional[int] = None,
    model: Optional[str] = None
) -> List[List[float]]:
    """
    Generate embeddings for text chunks using OpenAI API with batching.
    
    Args:
        chunks: List of text chunks
        batch_size: Number of chunks to process in a single API call (default from settings)
        model: The model to use for embeddings (default from settings)
        
    Returns:
        List of embedding vectors as raw float arrays
    """
    if not chunks:
        # logger.warning("No chunks provided for embedding generation") # Replaced
        # WARNING: No chunks provided for embedding generation
        return []
        
    # Use defaults from settings if not provided
    batch_size = batch_size or min(settings.EMBEDDING_BATCH_SIZE, 5)  # Default smaller batch size for faster responses
    model = model or settings.OPENAI_EMBEDDING_MODEL
    
    # Use a smaller model if available - faster and less likely to hit token limits
    if model == "text-embedding-ada-002":
        # Can switch to text-embedding-3-small if you want even faster (but slightly less accurate) results
        model = model  # Keep as-is for now, but this is where you'd switch models if needed
    
    # Validate and prepare chunks
    validated_chunks = prepare_chunks_for_embedding(chunks, model)
    if len(validated_chunks) != len(chunks):
        # logger.info(f"Validated {len(validated_chunks)}/{len(chunks)} chunks for embedding") # Replaced
        # INFO: Validated {len(validated_chunks)}/{len(chunks)} chunks for embedding
        pass  # Added pass to avoid empty if-block syntax error
    
    # Early exit if we only need to embed a single chunk (direct API call)
    if len(validated_chunks) == 1:
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await _create_embeddings_with_retry(
            client=client,
            batch=validated_chunks,
            model=model
        )
        return [response.data[0].embedding]
        
    embeddings = []
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    try:
        # Process in batches
        for i in range(0, len(validated_chunks), batch_size):
            batch = validated_chunks[i:i+batch_size]
            batch_size_actual = len(batch)
            # logger.info(f"Processing batch {i//batch_size + 1}: {batch_size_actual} chunks") # Replaced
            # INFO: Processing batch {i//batch_size + 1}: {batch_size_actual} chunks
            
            # Get embeddings for the batch
            response = await _create_embeddings_with_retry(
                client=client,
                batch=batch,
                model=model
            )
            
            # Process each embedding in the response
            for j, embedding_data in enumerate(response.data):
                # Store as raw vector (List[float])
                embeddings.append(embedding_data.embedding)
                
            # Use a minimal delay between batches (0.1s instead of 0.5s)
            if batch_size_actual == batch_size and i + batch_size < len(validated_chunks):
                await asyncio.sleep(0.1)
        
        # logger.info(f"Successfully generated {len(embeddings)} embeddings") # Replaced
        # INFO: Successfully generated {len(embeddings)} embeddings
        return embeddings
        
    except Exception as e:
        # logger.error(f"Error generating embeddings: {str(e)}", exc_info=True) # Replaced
        # ERROR: Error generating embeddings: {str(e)} # Add exc_info=True if needed for debugging
        raise HTTPException(status_code=500, detail="Failed to generate embeddings") from e

async def process_document(
    content: Union[str, bytes], 
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    batch_size: Optional[int] = None,
    model: Optional[str] = None
) -> Tuple[List[str], List[List[float]], Dict[str, Any]]:
    """
    Process document content into chunks and generate embeddings.
    
    Args:
        content: Raw document text content (string or bytes)
        chunk_size: Custom chunk size in tokens
        chunk_overlap: Custom overlap size in tokens
        batch_size: Custom embedding API batch size
        model: Custom embedding model
        
    Returns:
        Tuple of (text_chunks, embeddings, stats)
    """
    # Type and content validation
    if content is None:
        raise ValueError("Content cannot be None")
        
    # Handle potential bytes content
    if isinstance(content, bytes):
        # logger.warning("Content was bytes and required fallback decoding to latin-1") # Replaced
        # WARNING: Content was bytes and required fallback decoding to latin-1
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            text_content = content.decode('latin-1')
    else:
        text_content = content
        
    if not text_content or len(text_content.strip()) == 0:
        # logger.warning("Content is empty or whitespace only") # Replaced
        # WARNING: Content is empty or whitespace only
        return [], [], {"total_tokens": 0, "chunk_count": 0, "avg_chunk_tokens": 0}
    
    # Chunk the text
    chunks, stats = chunk_text(
        text_content, 
        chunk_size=chunk_size, 
        overlap=chunk_overlap, 
        model=model
    )


    # Generate embeddings
    embeddings = await generate_embeddings(
        chunks,
        batch_size=batch_size,
        model=model
    )
    
    return chunks, embeddings, stats