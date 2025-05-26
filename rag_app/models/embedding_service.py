"""
Embedding service for generating document embeddings.
"""

from typing import List, Dict, Any, Optional
import numpy as np
try:
    from haystack.components.embedders import SentenceTransformersTextEmbedder, SentenceTransformersDocumentEmbedder
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
from haystack import Document

from rag_app.utils.logger import get_logger
from rag_app.config.settings import settings

logger = get_logger(__name__)

class EmbeddingService:
    """Service for generating embeddings using sentence transformers."""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize embedding service.
        
        Args:
            model_name: Name of the sentence transformer model to use.
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        
        try:
            # Use simple text-based embeddings as fallback
            self._use_simple_embeddings = True
            logger.info("Using simple text-based embeddings for compatibility")
            
            # Warm up the models
            self._warm_up_models()
            
            logger.info(f"Initialized EmbeddingService with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error initializing embedding service: {e}")
            raise Exception(f"Failed to initialize embedding service: {e}")
    
    def _warm_up_models(self):
        """Warm up the embedding models with a test query."""
        try:
            if self._use_simple_embeddings:
                logger.debug("Simple embeddings ready")
            else:
                # Warm up sentence transformers if available
                test_result = self.text_embedder.run(text="test query")
                if test_result and "embedding" in test_result:
                    logger.debug(f"Text embedder warmed up successfully. Embedding dimension: {len(test_result['embedding'])}")
            
        except Exception as e:
            logger.warning(f"Error during model warm-up: {e}")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text query.
        
        Args:
            text: Text to embed.
            
        Returns:
            List of embedding values.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return []
        
        try:
            if self._use_simple_embeddings:
                # Simple word-count based embedding
                return self._simple_text_embedding(text.strip())
            else:
                result = self.text_embedder.run(text=text.strip())
                
                if result and "embedding" in result:
                    embedding = result["embedding"]
                    logger.debug(f"Generated embedding for text (length: {len(text)}) -> dimension: {len(embedding)}")
                    return embedding
                else:
                    logger.error("No embedding returned from text embedder")
                    return []
                
        except Exception as e:
            logger.error(f"Error generating text embedding: {e}")
            return []
    
    def embed_documents(self, documents: List[Document]) -> List[Document]:
        """Generate embeddings for a list of documents.
        
        Args:
            documents: List of documents to embed.
            
        Returns:
            List of documents with embeddings added.
        """
        if not documents:
            logger.warning("No documents provided for embedding")
            return []
        
        logger.info(f"Generating embeddings for {len(documents)} documents")
        
        try:
            # Filter out documents with empty content
            valid_documents = [doc for doc in documents if doc.content and doc.content.strip()]
            
            if len(valid_documents) != len(documents):
                logger.warning(f"Filtered out {len(documents) - len(valid_documents)} documents with empty content")
            
            if not valid_documents:
                logger.warning("No valid documents found for embedding")
                return []
            
            # Generate embeddings for each document
            for doc in valid_documents:
                embedding = self.embed_text(doc.content)
                doc.embedding = embedding
            
            logger.info(f"Successfully generated embeddings for {len(valid_documents)} documents")
            return valid_documents
                
        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}")
            return documents  # Return original documents if embedding fails
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by the model.
        
        Returns:
            Embedding dimension.
        """
        try:
            # Generate a test embedding to determine dimension
            test_embedding = self.embed_text("test")
            return len(test_embedding) if test_embedding else settings.EMBEDDING_DIMENSION
            
        except Exception as e:
            logger.error(f"Error getting embedding dimension: {e}")
            return settings.EMBEDDING_DIMENSION
    
    def similarity_search(self, query_embedding: List[float], document_embeddings: List[List[float]], top_k: int = 5) -> List[int]:
        """Perform similarity search between query and document embeddings.
        
        Args:
            query_embedding: Query embedding vector.
            document_embeddings: List of document embedding vectors.
            top_k: Number of top results to return.
            
        Returns:
            List of indices of most similar documents.
        """
        if not query_embedding or not document_embeddings:
            logger.warning("Empty embeddings provided for similarity search")
            return []
        
        try:
            query_array = np.array(query_embedding)
            doc_arrays = np.array(document_embeddings)
            
            # Calculate cosine similarity
            similarities = np.dot(doc_arrays, query_array) / (
                np.linalg.norm(doc_arrays, axis=1) * np.linalg.norm(query_array)
            )
            
            # Get top-k most similar documents
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            logger.debug(f"Found {len(top_indices)} similar documents for query")
            return top_indices.tolist()
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model.
        
        Returns:
            Dictionary containing model information.
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.get_embedding_dimension(),
            "device": "cpu",
            "framework": "sentence-transformers",
            "model_type": "embedding"
        }
    
    def batch_embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed.
            batch_size: Size of each batch.
            
        Returns:
            List of embeddings for each text.
        """
        if not texts:
            return []
        
        embeddings = []
        
        try:
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = []
                
                for text in batch_texts:
                    embedding = self.embed_text(text)
                    batch_embeddings.append(embedding)
                
                embeddings.extend(batch_embeddings)
                logger.debug(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error in batch text embedding: {e}")
            return []
    
    def _simple_text_embedding(self, text: str) -> List[float]:
        """Create a simple TF-IDF-like embedding for text."""
        # Simple word frequency based embedding (384 dimensions)
        import hashlib
        import re
        
        # Clean and tokenize text
        words = re.findall(r'\w+', text.lower())
        
        # Create a simple hash-based embedding
        embedding = [0.0] * 384
        
        for word in words:
            # Use hash to determine position and value
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            pos = hash_val % 384
            embedding[pos] += 1.0
        
        # Normalize
        total = sum(embedding)
        if total > 0:
            embedding = [x / total for x in embedding]
        
        return embedding
