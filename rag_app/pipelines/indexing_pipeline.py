"""
Document indexing pipeline for RAG application.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from haystack import Document, Pipeline
from haystack.components.writers import DocumentWriter

from rag_app.data_ingestion.pdf_loader import PDFLoader
from rag_app.data_ingestion.document_preprocessor import DocumentPreprocessor
from rag_app.models.embedding_service import EmbeddingService
from rag_app.document_store.local_document_store import LocalDocumentStore
from rag_app.utils.logger import get_logger
from rag_app.config.settings import settings

logger = get_logger(__name__)

class IndexingPipeline:
    """Pipeline for indexing PDF documents with embeddings."""
    
    def __init__(self, document_store: Optional[LocalDocumentStore] = None):
        """Initialize indexing pipeline.
        
        Args:
            document_store: Document store instance. If None, creates new one.
        """
        self.document_store = document_store or LocalDocumentStore()
        self.pdf_loader = PDFLoader()
        self.preprocessor = DocumentPreprocessor()
        self.embedding_service = EmbeddingService()
        
        # Initialize Haystack pipeline
        self._init_pipeline()
        
        logger.info("Initialized IndexingPipeline")
    
    def _init_pipeline(self):
        """Initialize the Haystack indexing pipeline."""
        try:
            # Create pipeline
            self.pipeline = Pipeline()
            
            # Note: We'll use our custom components instead of Haystack's built-in ones
            # for more control over the process
            
            logger.debug("Indexing pipeline initialized")
            
        except Exception as e:
            logger.error(f"Error initializing indexing pipeline: {e}")
            raise Exception(f"Failed to initialize indexing pipeline: {e}")
    
    def index_documents_from_directory(self, directory_path: Optional[Path] = None) -> Dict[str, Any]:
        """Index all PDF documents from a directory.
        
        Args:
            directory_path: Directory containing PDF files. Uses settings.DATA_DIR if None.
            
        Returns:
            Dictionary containing indexing results and statistics.
        """
        data_dir = directory_path or settings.DATA_DIR
        
        logger.info(f"Starting document indexing from directory: {data_dir}")
        
        try:
            # Step 1: Load PDF documents
            logger.info("Step 1: Loading PDF documents...")
            documents = self.pdf_loader.load_all_pdfs()
            
            if not documents:
                logger.warning("No documents loaded from PDFs")
                return {
                    "success": False,
                    "message": "No documents found to index",
                    "documents_processed": 0,
                    "chunks_created": 0
                }
            
            # Step 2: Index the loaded documents
            return self.index_documents(documents)
            
        except Exception as e:
            logger.error(f"Error indexing documents from directory: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents_processed": 0,
                "chunks_created": 0
            }
    
    def index_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """Index a list of documents.
        
        Args:
            documents: List of documents to index.
            
        Returns:
            Dictionary containing indexing results and statistics.
        """
        if not documents:
            logger.warning("No documents provided for indexing")
            return {
                "success": False,
                "message": "No documents provided",
                "documents_processed": 0,
                "chunks_created": 0
            }
        
        logger.info(f"Starting indexing of {len(documents)} documents")
        
        try:
            # Step 1: Preprocess documents (clean and chunk)
            logger.info("Step 1: Preprocessing documents...")
            preprocessed_docs = self.preprocessor.preprocess_documents(documents)
            
            if not preprocessed_docs:
                logger.error("No documents remained after preprocessing")
                return {
                    "success": False,
                    "message": "All documents filtered out during preprocessing",
                    "documents_processed": len(documents),
                    "chunks_created": 0
                }
            
            # Step 2: Generate embeddings
            logger.info("Step 2: Generating embeddings...")
            embedded_docs = self.embedding_service.embed_documents(preprocessed_docs)
            
            if not embedded_docs:
                logger.error("No embeddings generated for documents")
                return {
                    "success": False,
                    "message": "Failed to generate embeddings",
                    "documents_processed": len(documents),
                    "chunks_created": len(preprocessed_docs)
                }
            
            # Step 3: Store documents and embeddings
            logger.info("Step 3: Storing documents in document store...")
            self.document_store.write_documents(embedded_docs)
            
            # Step 4: Get statistics
            stats = self.preprocessor.get_preprocessing_stats(documents, preprocessed_docs)
            
            logger.info(f"Successfully indexed {len(documents)} documents into {len(embedded_docs)} chunks")
            
            return {
                "success": True,
                "message": f"Successfully indexed {len(documents)} documents",
                "documents_processed": len(documents),
                "chunks_created": len(embedded_docs),
                "chunks_with_embeddings": len([doc for doc in embedded_docs if hasattr(doc, 'embedding') and doc.embedding]),
                "preprocessing_stats": stats,
                "store_info": self.document_store.get_store_info()
            }
            
        except Exception as e:
            logger.error(f"Error during document indexing: {e}")
            return {
                "success": False,
                "error": str(e),
                "documents_processed": len(documents),
                "chunks_created": 0
            }
    
    def index_single_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Index a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Dictionary containing indexing results.
        """
        logger.info(f"Indexing single PDF: {pdf_path}")
        
        try:
            # Load the PDF
            documents = self.pdf_loader.load_pdf(pdf_path)
            
            if not documents:
                return {
                    "success": False,
                    "message": f"No content extracted from PDF: {pdf_path}",
                    "file_path": str(pdf_path)
                }
            
            # Index the documents
            result = self.index_documents(documents)
            result["file_path"] = str(pdf_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error indexing PDF {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": str(pdf_path)
            }
    
    def reindex_all_documents(self) -> Dict[str, Any]:
        """Reindex all documents by clearing the store and reprocessing all PDFs.
        
        Returns:
            Dictionary containing reindexing results.
        """
        logger.info("Starting complete reindexing of all documents")
        
        try:
            # Get current document count for comparison
            current_count = self.document_store.count_documents()
            
            # Clear existing documents (optional - comment out if you want to keep old docs)
            # Note: Uncomment the next line if you want to clear the store before reindexing
            # self._clear_document_store()
            
            # Reindex all documents from directory
            result = self.index_documents_from_directory()
            
            if result["success"]:
                result["previous_document_count"] = current_count
                result["reindexing"] = True
                
            return result
            
        except Exception as e:
            logger.error(f"Error during reindexing: {e}")
            return {
                "success": False,
                "error": str(e),
                "reindexing": True
            }
    
    def _clear_document_store(self):
        """Clear all documents from the document store."""
        try:
            # Get all document IDs
            all_docs = self.document_store.get_all_documents()
            doc_ids = [doc.id for doc in all_docs if hasattr(doc, 'id')]
            
            if doc_ids:
                self.document_store.delete_documents(doc_ids)
                logger.info(f"Cleared {len(doc_ids)} documents from store")
            
        except Exception as e:
            logger.error(f"Error clearing document store: {e}")
    
    def get_indexing_status(self) -> Dict[str, Any]:
        """Get current indexing status and statistics.
        
        Returns:
            Dictionary containing indexing status information.
        """
        try:
            store_info = self.document_store.get_store_info()
            
            # Count available PDF files
            pdf_files = list(settings.DATA_DIR.glob("*.pdf")) if settings.DATA_DIR.exists() else []
            
            return {
                "total_pdf_files": len(pdf_files),
                "indexed_documents": store_info.get("total_documents", 0),
                "store_info": store_info,
                "embedding_model": self.embedding_service.get_model_info(),
                "data_directory": str(settings.DATA_DIR),
                "index_status": "ready" if store_info.get("total_documents", 0) > 0 else "empty"
            }
            
        except Exception as e:
            logger.error(f"Error getting indexing status: {e}")
            return {
                "error": str(e),
                "index_status": "error"
            }
    
    def validate_index(self) -> Dict[str, Any]:
        """Validate the current document index.
        
        Returns:
            Dictionary containing validation results.
        """
        try:
            # Get all documents
            all_docs = self.document_store.get_all_documents()
            
            # Count documents with and without embeddings
            docs_with_embeddings = 0
            docs_without_embeddings = 0
            
            for doc in all_docs:
                if hasattr(doc, 'embedding') and doc.embedding:
                    docs_with_embeddings += 1
                else:
                    docs_without_embeddings += 1
            
            validation_result = {
                "total_documents": len(all_docs),
                "documents_with_embeddings": docs_with_embeddings,
                "documents_without_embeddings": docs_without_embeddings,
                "embedding_coverage": docs_with_embeddings / len(all_docs) if all_docs else 0,
                "index_valid": docs_without_embeddings == 0 and len(all_docs) > 0
            }
            
            if validation_result["index_valid"]:
                logger.info("Index validation successful")
            else:
                logger.warning("Index validation found issues")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error during index validation: {e}")
            return {
                "error": str(e),
                "index_valid": False
            }
