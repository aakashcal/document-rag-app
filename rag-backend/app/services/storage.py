import os
from fastapi import UploadFile
from pathlib import Path
# import logging # Removed
import fitz  # PyMuPDF for reading PDFs

# Configure logging for this module
# logger = logging.getLogger(__name__) # Removed

# Directory where uploaded files will be saved
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)  # Create if it doesn't exist

async def save_uploaded_document(file: UploadFile) -> str:
    """
    Saves the uploaded file to the uploads directory.
    
    Args:
        file (UploadFile): File uploaded via FastAPI.
    
    Returns:
        str: Full path to the saved file.
    """
    filepath = UPLOAD_DIR / file.filename
    with open(filepath, "wb") as f:
        content = await file.read()  # Read file content asynchronously
        f.write(content)             # Write to disk
    # logger.info(f"Saved file to {filepath}") # Replaced
    # INFO: Saved file to {filepath}
    return str(filepath)

async def read_document_content(filepath: str) -> str:
    """
    Reads the content of a text or PDF file.
    Handles UTF-8, latin-1, and binary fallbacks.

    Args:
        filepath (str): Path to the file.
    
    Returns:
        str: Extracted or decoded text content from the file.
    """
    # logger.info(f"Reading content from {filepath}") # Replaced
    # INFO: Reading content from {filepath}

    # If it's a PDF file, extract text using PyMuPDF
    if filepath.lower().endswith(".pdf"):
        # logger.info(f"Detected PDF file: {filepath}") # Replaced
        # INFO: Detected PDF file: {filepath}
        return extract_text_from_pdf(filepath)

    try:
        # Try reading with UTF-8 encoding
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            # logger.info(f"Successfully read {len(content)} characters with UTF-8 encoding") # Replaced
            # INFO: Successfully read {len(content)} characters with UTF-8 encoding
            return content
    except UnicodeDecodeError:
        # Fallback: Try latin-1 encoding
        # logger.warning(f"UTF-8 decode failed, falling back to latin-1 for {filepath}") # Replaced
        # WARNING: UTF-8 decode failed, falling back to latin-1 for {filepath}
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                content = f.read()
                # logger.info(f"Successfully read {len(content)} characters with latin-1 encoding") # Replaced
                # INFO: Successfully read {len(content)} characters with latin-1 encoding
                return content
        except Exception as e:
            # logger.error(f"Failed to read file with latin-1 encoding: {str(e)}") # Replaced
            # ERROR: Failed to read file with latin-1 encoding: {str(e)}
            # Final fallback: Read as binary and decode ignoring errors
            with open(filepath, "rb") as f:
                binary_content = f.read()
                text_content = binary_content.decode('utf-8', errors='ignore')
                # logger.warning(f"Used binary read with error ignoring, got {len(text_content)} characters") # Replaced
                # WARNING: Used binary read with error ignoring, got {len(text_content)} characters
                return text_content

def extract_text_from_pdf(filepath: str) -> str:
    """
    Extracts all text from a PDF file using PyMuPDF.

    Args:
        filepath (str): Path to the PDF file.
    
    Returns:
        str: Combined text from all pages.
    """
    try:
        doc = fitz.open(filepath)  # Open PDF file
        text = ""
        for page in doc:
            text += page.get_text()  # Extract text page-by-page
        # logger.info(f"Extracted {len(text)} characters from PDF: {filepath}") # Replaced
        # INFO: Extracted {len(text)} characters from PDF: {filepath}
        return text
    except Exception as e:
        # logger.error(f"Failed to extract text from PDF: {e}") # Replaced
        # ERROR: Failed to extract text from PDF: {e}
        return ""
