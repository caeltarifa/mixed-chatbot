"""
Local document store implementation using SQLite and Haystack.
"""

import sqlite3
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import numpy as np
from haystack import Document
from haystack.document_stores.in_memory import InMemoryDocumentStore

from rag_app.utils.logger import get_logger
from rag_app.config.settings import settings

logger = get_logger(__name__)

class LocalDocumentStore:
    """Local document store with SQLite backend and vector search capabilities."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize local document store.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path or settings.DATABASE_PATH
        self.db_dir = Path(self.db_path).parent
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize InMemoryDocumentStore for vector operations
        self.vector_store = InMemoryDocumentStore()
        
        # Initialize SQLite database
        self._init_database()
        
        logger.info(f"Initialized LocalDocumentStore with database: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create documents table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        content TEXT NOT NULL,
                        meta TEXT,
                        embedding BLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for faster searches
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_documents_meta 
                    ON documents(meta)
                """)
                
                # Create embeddings table for vector search metadata
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings_metadata (
                        id INTEGER PRIMARY KEY,
                        model_name TEXT NOT NULL,
                        embedding_dimension INTEGER NOT NULL,
                        total_documents INTEGER DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Database tables initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise Exception(f"Database initialization failed: {e}")
    
    def write_documents(self, documents: List[Document], policy: str = "overwrite") -> None:
        """Write documents to both SQLite and vector store.
        
        Args:
            documents: List of documents to store.
            policy: Write policy ('overwrite' or 'duplicate_skip').
        """
        if not documents:
            logger.warning("No documents provided for writing")
            return
        
        logger.info(f"Writing {len(documents)} documents to store with policy: {policy}")
        
        try:
            # Write to vector store for embedding search
            self.vector_store.write_documents(documents, policy=policy)
            
            # Write to SQLite for persistence
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for doc in documents:
                    doc_id = doc.id if hasattr(doc, 'id') and doc.id else self._generate_doc_id(doc)
                    meta_json = json.dumps(doc.meta) if doc.meta else "{}"
                    
                    if policy == "overwrite":
                        cursor.execute("""
                            INSERT OR REPLACE INTO documents (id, content, meta)
                            VALUES (?, ?, ?)
                        """, (doc_id, doc.content, meta_json))
                    else:  # duplicate_skip
                        cursor.execute("""
                            INSERT OR IGNORE INTO documents (id, content, meta)
                            VALUES (?, ?, ?)
                        """, (doc_id, doc.content, meta_json))
                
                conn.commit()
            
            logger.info(f"Successfully wrote {len(documents)} documents to store")
            
        except Exception as e:
            logger.error(f"Error writing documents: {e}")
            raise Exception(f"Failed to write documents: {e}")
    
    def get_all_documents(self) -> List[Document]:
        """Retrieve all documents from the store.
        
        Returns:
            List of all documents in the store.
        """
        try:
            # Get from vector store (which has embeddings)
            vector_docs = self.vector_store.filter_documents()
            
            if vector_docs:
                logger.info(f"Retrieved {len(vector_docs)} documents from vector store")
                return vector_docs
            
            # Fallback to SQLite if vector store is empty
            return self._get_documents_from_sqlite()
            
        except Exception as e:
            logger.error(f"Error retrieving all documents: {e}")
            return []
    
    def _get_documents_from_sqlite(self) -> List[Document]:
        """Retrieve documents from SQLite database.
        
        Returns:
            List of documents from SQLite.
        """
        documents = []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, content, meta FROM documents")
                rows = cursor.fetchall()
                
                for row in rows:
                    doc_id, content, meta_json = row
                    meta = json.loads(meta_json) if meta_json else {}
                    
                    document = Document(content=content, meta=meta)
                    if hasattr(document, 'id'):
                        document.id = doc_id
                    
                    documents.append(document)
                
                logger.info(f"Retrieved {len(documents)} documents from SQLite")
                
        except Exception as e:
            logger.error(f"Error retrieving documents from SQLite: {e}")
        
        return documents
    
    def filter_documents(self, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Filter documents based on metadata criteria.
        
        Args:
            filters: Dictionary of filter criteria.
            
        Returns:
            List of filtered documents.
        """
        try:
            # Use vector store filtering if available
            if hasattr(self.vector_store, 'filter_documents'):
                return self.vector_store.filter_documents(filters=filters)
            
            # Fallback implementation
            all_docs = self.get_all_documents()
            if not filters:
                return all_docs
            
            filtered_docs = []
            for doc in all_docs:
                if self._document_matches_filters(doc, filters):
                    filtered_docs.append(doc)
            
            logger.info(f"Filtered {len(filtered_docs)} documents from {len(all_docs)} total")
            return filtered_docs
            
        except Exception as e:
            logger.error(f"Error filtering documents: {e}")
            return []
    
    def _document_matches_filters(self, document: Document, filters: Dict[str, Any]) -> bool:
        """Check if document matches filter criteria.
        
        Args:
            document: Document to check.
            filters: Filter criteria.
            
        Returns:
            True if document matches filters.
        """
        if not document.meta or not filters:
            return True
        
        for key, value in filters.items():
            if key not in document.meta:
                return False
            
            if isinstance(value, list):
                if document.meta[key] not in value:
                    return False
            else:
                if document.meta[key] != value:
                    return False
        
        return True
    
    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents by their IDs.
        
        Args:
            document_ids: List of document IDs to delete.
        """
        if not document_ids:
            logger.warning("No document IDs provided for deletion")
            return
        
        try:
            # Delete from vector store
            self.vector_store.delete_documents(document_ids)
            
            # Delete from SQLite
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                placeholders = ",".join(["?" for _ in document_ids])
                cursor.execute(f"DELETE FROM documents WHERE id IN ({placeholders})", document_ids)
                conn.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"Deleted {deleted_count} documents from store")
                
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise Exception(f"Failed to delete documents: {e}")
    
    def count_documents(self) -> int:
        """Count total number of documents in the store.
        
        Returns:
            Total number of documents.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM documents")
                count = cursor.fetchone()[0]
                return count
                
        except Exception as e:
            logger.error(f"Error counting documents: {e}")
            return 0
    
    def get_store_info(self) -> Dict[str, Any]:
        """Get information about the document store.
        
        Returns:
            Dictionary containing store information.
        """
        try:
            document_count = self.count_documents()
            
            # Get database file size
            db_size = Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
            
            # Get vector store info
            vector_count = len(self.vector_store.filter_documents()) if hasattr(self.vector_store, 'filter_documents') else 0
            
            return {
                "database_path": self.db_path,
                "database_size_bytes": db_size,
                "total_documents": document_count,
                "vector_store_documents": vector_count,
                "store_type": "LocalDocumentStore",
                "backend": "SQLite + InMemoryDocumentStore"
            }
            
        except Exception as e:
            logger.error(f"Error getting store info: {e}")
            return {"error": str(e)}
    
    def _generate_doc_id(self, document: Document) -> str:
        """Generate a unique ID for a document.
        
        Args:
            document: Document to generate ID for.
            
        Returns:
            Generated document ID.
        """
        import hashlib
        content_hash = hashlib.md5(document.content.encode()).hexdigest()
        meta_hash = hashlib.md5(str(document.meta).encode()).hexdigest() if document.meta else "nometa"
        return f"doc_{content_hash[:8]}_{meta_hash[:8]}"
    
    def sync_stores(self) -> None:
        """Synchronize SQLite and vector store."""
        try:
            # Always load documents from SQLite to vector store to ensure embeddings are available
            sqlite_docs = self._get_documents_from_sqlite()
            if sqlite_docs:
                # Check if documents have embeddings and add them if missing
                for doc in sqlite_docs:
                    if not hasattr(doc, 'embedding') or not doc.embedding:
                        # Generate embedding if missing
                        from rag_app.models.embedding_service import EmbeddingService
                        embedding_service = EmbeddingService()
                        doc.embedding = embedding_service.embed_text(doc.content)
                
                self.vector_store.write_documents(sqlite_docs)
                logger.info(f"Synchronized {len(sqlite_docs)} documents from SQLite to vector store")
                    
        except Exception as e:
            logger.error(f"Error synchronizing stores: {e}")
