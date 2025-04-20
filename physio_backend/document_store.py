import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from haystack.document_stores import InMemoryDocumentStore
from haystack.schema import Document

# Configure logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Path to the physiotherapy data file
PHYSIO_DATA_PATH = Path(__file__).parent / "documents" / "physiotherapy_data.txt"

def load_documents_from_file(file_path: Path) -> List[Document]:
    """
    Load documents from a text file, splitting it into smaller chunks
    
    Args:
        file_path: Path to the text file
        
    Returns:
        List of Document objects
    """
    logger.info(f"Loading documents from {file_path}")
    
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        # Return a single document with basic information if file doesn't exist
        return [Document(
            content="Physiotherapy is a healthcare profession that works with people to identify and maximize their ability to move and function throughout their lifespan.",
            meta={"source": "default"}
        )]
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Split content into paragraphs and create Document objects
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        documents = []
        
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) < 20:  # Skip very short paragraphs
                continue
                
            doc = Document(
                content=paragraph,
                meta={
                    "source": str(file_path),
                    "paragraph_id": i
                }
            )
            documents.append(doc)
            
        logger.info(f"Loaded {len(documents)} documents")
        return documents
        
    except Exception as e:
        logger.error(f"Error loading documents: {str(e)}")
        return [Document(
            content="Physiotherapy helps restore movement and function when someone is affected by injury, illness or disability.",
            meta={"source": "default"}
        )]

def initialize_document_store() -> InMemoryDocumentStore:
    """
    Initialize and populate the document store with physiotherapy data
    
    Returns:
        InMemoryDocumentStore: The initialized document store
    """
    # Initialize document store
    document_store = InMemoryDocumentStore(use_bm25=True)
    
    # Load documents
    documents = load_documents_from_file(PHYSIO_DATA_PATH)
    
    # Write documents to document store
    document_store.write_documents(documents)
    
    # Update embeddings if needed (not using embeddings in this example)
    
    return document_store
