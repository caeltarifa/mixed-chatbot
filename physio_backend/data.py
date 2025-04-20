import os
import logging
from pathlib import Path
import re
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Path to the physiotherapy data file
PHYSIO_DATA_PATH = Path(__file__).parent / "documents" / "physiotherapy_data.txt"

class PhysioDocument:
    """A document containing physiotherapy information"""
    
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.metadata = metadata or {}

def load_documents() -> List[PhysioDocument]:
    """
    Load documents from the physiotherapy data file
    
    Returns:
        List of PhysioDocument objects
    """
    logger.info(f"Loading documents from {PHYSIO_DATA_PATH}")
    
    if not PHYSIO_DATA_PATH.exists():
        logger.warning(f"File not found: {PHYSIO_DATA_PATH}")
        # Return a single document with basic information if file doesn't exist
        return [PhysioDocument(
            content="Physiotherapy is a healthcare profession that works with people to identify and maximize their ability to move and function throughout their lifespan."
        )]
    
    try:
        with open(PHYSIO_DATA_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        documents = []
        
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) < 20:  # Skip very short paragraphs
                continue
                
            doc = PhysioDocument(
                content=paragraph,
                metadata={
                    "source": str(PHYSIO_DATA_PATH),
                    "paragraph_id": i
                }
            )
            documents.append(doc)
            
        logger.info(f"Loaded {len(documents)} documents")
        return documents
        
    except Exception as e:
        logger.error(f"Error loading documents: {str(e)}")
        return [PhysioDocument(
            content="Physiotherapy helps restore movement and function when someone is affected by injury, illness or disability."
        )]

def simple_search(query: str, documents: List[PhysioDocument], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a simple keyword-based search on the documents
    
    Args:
        query: The search query
        documents: List of documents to search
        top_k: Number of top results to return
        
    Returns:
        List of search results with document content and score
    """
    logger.info(f"Searching for: {query}")
    
    # Normalize query
    query = query.lower()
    query_terms = set(re.findall(r'\w+', query))
    
    # Score documents based on term overlap
    results = []
    for doc in documents:
        content = doc.content.lower()
        content_terms = set(re.findall(r'\w+', content))
        
        # Calculate term overlap score
        matching_terms = query_terms.intersection(content_terms)
        if matching_terms:
            score = len(matching_terms) / len(query_terms)
            
            # Boost score if query terms appear close to each other
            for term in query_terms:
                if term in content:
                    score *= 1.2
            
            results.append({
                "content": doc.content,
                "score": min(score, 1.0),
                "metadata": doc.metadata
            })
    
    # Sort by score and return top k results
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]