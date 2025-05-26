"""
Main RAG service orchestrating all components.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from rag_app.document_store.local_document_store import LocalDocumentStore
from rag_app.models.embedding_service import EmbeddingService
from rag_app.models.generative_service import GenerativeService
from rag_app.pipelines.indexing_pipeline import IndexingPipeline
from rag_app.pipelines.query_pipeline import QueryPipeline
from rag_app.utils.logger import get_logger
from rag_app.config.settings import settings

logger = get_logger(__name__)

class RAGService:
    """Main RAG service for orchestrating document processing and querying."""
    
    def __init__(self):
        """Initialize RAG service with all components."""
        logger.info("Initializing RAG Service...")
        
        try:
            # Validate settings
            settings.validate_settings()
            
            # Initialize core components
            self.document_store = LocalDocumentStore()
            self.embedding_service = EmbeddingService()
            self.generative_service = GenerativeService()
            
            # Initialize pipelines
            self.indexing_pipeline = IndexingPipeline(self.document_store)
            self.query_pipeline = QueryPipeline(
                self.document_store, 
                self.embedding_service, 
                self.generative_service
            )
            
            # Service state
            self._initialized = True
            
            logger.info("RAG Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG Service: {e}")
            self._initialized = False
            raise Exception(f"Failed to initialize RAG Service: {e}")
    
    def is_ready(self) -> bool:
        """Check if the RAG service is ready for use.
        
        Returns:
            True if service is initialized and has indexed documents.
        """
        if not self._initialized:
            return False
        
        try:
            doc_count = self.document_store.count_documents()
            return doc_count > 0
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the RAG service.
        
        Returns:
            Dictionary containing service status information.
        """
        try:
            status = {
                "service_initialized": self._initialized,
                "service_ready": self.is_ready(),
                "timestamp": self._get_timestamp()
            }
            
            if self._initialized:
                status.update({
                    "indexing_status": self.indexing_pipeline.get_indexing_status(),
                    "query_pipeline_status": self.query_pipeline.get_pipeline_status(),
                    "document_count": self.document_store.count_documents(),
                    "store_info": self.document_store.get_store_info()
                })
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {
                "service_initialized": False,
                "error": str(e),
                "timestamp": self._get_timestamp()
            }
    
    def index_documents(self, force_reindex: bool = False) -> Dict[str, Any]:
        """Index all PDF documents from the data directory.
        
        Args:
            force_reindex: Whether to force reindexing even if documents exist.
            
        Returns:
            Dictionary containing indexing results.
        """
        logger.info(f"Starting document indexing (force_reindex={force_reindex})")
        
        try:
            # Check if documents already exist
            current_count = self.document_store.count_documents()
            
            if current_count > 0 and not force_reindex:
                logger.info(f"Documents already indexed ({current_count} documents). Use force_reindex=True to reindex.")
                return {
                    "success": True,
                    "message": f"Documents already indexed ({current_count} documents)",
                    "documents_processed": 0,
                    "existing_documents": current_count,
                    "skipped_indexing": True
                }
            
            # Perform indexing
            if force_reindex:
                result = self.indexing_pipeline.reindex_all_documents()
            else:
                result = self.indexing_pipeline.index_documents_from_directory()
            
            return result
            
        except Exception as e:
            logger.error(f"Error during document indexing: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents_processed": 0
            }
    
    def query(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """Process a query and return answer with sources.
        
        Args:
            question: User question.
            top_k: Number of relevant documents to consider.
            
        Returns:
            Dictionary containing answer, sources, and metadata.
        """
        if not self.is_ready():
            return {
                "question": question,
                "answer": "The RAG service is not ready. Please ensure documents are indexed first.",
                "sources": [],
                "success": False,
                "error": "Service not ready"
            }
        
        return self.query_pipeline.query(question, top_k)
    
    def search_documents(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for relevant documents without generating an answer.
        
        Args:
            query: Search query.
            top_k: Number of results to return.
            
        Returns:
            List of search result dictionaries.
        """
        if not self.is_ready():
            logger.warning("RAG service not ready for document search")
            return []
        
        return self.query_pipeline.search_documents(query, top_k)
    
    def ask_direct(self, question: str) -> Dict[str, Any]:
        """Ask a question directly to the LLM without document context.
        
        Args:
            question: Question to ask.
            
        Returns:
            Dictionary containing response and metadata.
        """
        if not self._initialized:
            return {
                "question": question,
                "answer": "RAG service is not initialized.",
                "success": False,
                "error": "Service not initialized"
            }
        
        return self.query_pipeline.ask_without_context(question)
    
    def get_document_summary(self, document_filter: Optional[Dict[str, Any]] = None) -> str:
        """Get a summary of indexed documents.
        
        Args:
            document_filter: Optional filter criteria for documents.
            
        Returns:
            Generated summary text.
        """
        if not self.is_ready():
            return "No documents available for summarization. Please index documents first."
        
        return self.query_pipeline.get_document_summary(document_filter)
    
    def add_pdf_document(self, pdf_path: Path) -> Dict[str, Any]:
        """Add and index a single PDF document.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Dictionary containing indexing results.
        """
        logger.info(f"Adding PDF document: {pdf_path}")
        
        try:
            result = self.indexing_pipeline.index_single_pdf(pdf_path)
            return result
            
        except Exception as e:
            logger.error(f"Error adding PDF document: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": str(pdf_path)
            }
    
    def validate_index(self) -> Dict[str, Any]:
        """Validate the current document index.
        
        Returns:
            Dictionary containing validation results.
        """
        return self.indexing_pipeline.validate_index()
    
    def get_available_pdfs(self) -> List[Dict[str, Any]]:
        """Get list of available PDF files in the data directory.
        
        Returns:
            List of PDF file information dictionaries.
        """
        try:
            pdf_files = []
            
            if settings.DATA_DIR.exists():
                for pdf_path in settings.DATA_DIR.glob("*.pdf"):
                    try:
                        file_info = {
                            "name": pdf_path.name,
                            "path": str(pdf_path),
                            "size_bytes": pdf_path.stat().st_size,
                            "exists": True
                        }
                        pdf_files.append(file_info)
                    except Exception as e:
                        logger.warning(f"Error getting info for PDF {pdf_path}: {e}")
            
            logger.info(f"Found {len(pdf_files)} PDF files in data directory")
            return pdf_files
            
        except Exception as e:
            logger.error(f"Error getting available PDFs: {e}")
            return []
    
    def clear_index(self) -> Dict[str, Any]:
        """Clear all indexed documents.
        
        Returns:
            Dictionary containing operation results.
        """
        logger.info("Clearing document index")
        
        try:
            # Get current count
            current_count = self.document_store.count_documents()
            
            if current_count == 0:
                return {
                    "success": True,
                    "message": "Index was already empty",
                    "documents_cleared": 0
                }
            
            # Get all document IDs and delete them
            all_docs = self.document_store.get_all_documents()
            doc_ids = [getattr(doc, 'id', f"doc_{i}") for i, doc in enumerate(all_docs)]
            
            if doc_ids:
                self.document_store.delete_documents(doc_ids)
            
            # Verify clearing
            remaining_count = self.document_store.count_documents()
            
            return {
                "success": remaining_count == 0,
                "message": f"Cleared {current_count - remaining_count} documents",
                "documents_cleared": current_count - remaining_count,
                "remaining_documents": remaining_count
            }
            
        except Exception as e:
            logger.error(f"Error clearing index: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents_cleared": 0
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of the RAG service.
        
        Returns:
            Dictionary containing health check results.
        """
        health_status = {
            "timestamp": self._get_timestamp(),
            "overall_healthy": True,
            "components": {}
        }
        
        try:
            # Check service initialization
            health_status["components"]["service"] = {
                "initialized": self._initialized,
                "ready": self.is_ready(),
                "healthy": self._initialized
            }
            
            # Check document store
            try:
                doc_count = self.document_store.count_documents()
                store_info = self.document_store.get_store_info()
                health_status["components"]["document_store"] = {
                    "accessible": True,
                    "document_count": doc_count,
                    "healthy": True,
                    "info": store_info
                }
            except Exception as e:
                health_status["components"]["document_store"] = {
                    "accessible": False,
                    "healthy": False,
                    "error": str(e)
                }
                health_status["overall_healthy"] = False
            
            # Check embedding service
            try:
                embedding_info = self.embedding_service.get_model_info()
                test_embedding = self.embedding_service.embed_text("test")
                health_status["components"]["embedding_service"] = {
                    "available": True,
                    "healthy": len(test_embedding) > 0,
                    "model_info": embedding_info
                }
                if len(test_embedding) == 0:
                    health_status["overall_healthy"] = False
            except Exception as e:
                health_status["components"]["embedding_service"] = {
                    "available": False,
                    "healthy": False,
                    "error": str(e)
                }
                health_status["overall_healthy"] = False
            
            # Check generative service
            try:
                generative_info = self.generative_service.get_model_info()
                health_status["components"]["generative_service"] = {
                    "available": True,
                    "healthy": generative_info.get("api_configured", False),
                    "model_info": generative_info
                }
                if not generative_info.get("api_configured", False):
                    health_status["overall_healthy"] = False
            except Exception as e:
                health_status["components"]["generative_service"] = {
                    "available": False,
                    "healthy": False,
                    "error": str(e)
                }
                health_status["overall_healthy"] = False
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return {
                "timestamp": self._get_timestamp(),
                "overall_healthy": False,
                "error": str(e)
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
