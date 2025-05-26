"""
Document preprocessing for RAG application.
"""

import re
from typing import List, Optional
from haystack import Document
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter

from rag_app.utils.logger import get_logger
from rag_app.config.settings import settings

logger = get_logger(__name__)

class DocumentPreprocessor:
    """Document preprocessing pipeline for cleaning and chunking documents."""
    
    def __init__(
        self, 
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        split_by: str = "sentence",
        split_length: Optional[int] = None
    ):
        """Initialize document preprocessor.
        
        Args:
            chunk_size: Maximum size of document chunks.
            chunk_overlap: Overlap between chunks.
            split_by: How to split documents ('sentence', 'word', 'passage').
            split_length: Length for splitting (overrides chunk_size if provided).
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.split_by = split_by
        self.split_length = split_length or self.chunk_size
        
        # Initialize Haystack components
        self.cleaner = DocumentCleaner(
            remove_empty_lines=True,
            remove_extra_whitespaces=True,
            remove_repeated_substrings=False,
        )
        
        self.splitter = DocumentSplitter(
            split_by=self.split_by,
            split_length=self.split_length,
            split_overlap=self.chunk_overlap,
            split_threshold=0
        )
        
        logger.info(f"Initialized DocumentPreprocessor with chunk_size={self.chunk_size}, "
                   f"overlap={self.chunk_overlap}, split_by={self.split_by}")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content.
        
        Args:
            text: Raw text content.
            
        Returns:
            Cleaned text content.
        """
        if not text:
            return ""
        
        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\/\n]', ' ', text)
        
        # Clean up multiple spaces
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def preprocess_documents(self, documents: List[Document]) -> List[Document]:
        """Preprocess a list of documents through cleaning and splitting.
        
        Args:
            documents: List of raw documents.
            
        Returns:
            List of preprocessed and chunked documents.
        """
        if not documents:
            logger.warning("No documents provided for preprocessing")
            return []
        
        logger.info(f"Preprocessing {len(documents)} documents")
        
        try:
            # Step 1: Clean documents
            logger.debug("Cleaning documents...")
            cleaned_documents = []
            
            for doc in documents:
                # Additional custom cleaning
                cleaned_content = self.clean_text(doc.content)
                
                if cleaned_content:  # Only keep non-empty documents
                    cleaned_doc = Document(
                        content=cleaned_content,
                        meta=doc.meta.copy() if doc.meta else {}
                    )
                    cleaned_documents.append(cleaned_doc)
            
            logger.info(f"After cleaning: {len(cleaned_documents)} documents remain")
            
            if not cleaned_documents:
                logger.warning("No documents remaining after cleaning")
                return []
            
            # Step 2: Use Haystack cleaner for additional cleaning
            cleaner_result = self.cleaner.run(documents=cleaned_documents)
            haystack_cleaned = cleaner_result["documents"]
            
            logger.info(f"After Haystack cleaning: {len(haystack_cleaned)} documents")
            
            # Step 3: Split documents into chunks
            logger.debug("Splitting documents into chunks...")
            try:
                self.splitter.warm_up()
            except AttributeError:
                pass  # Some components don't need warm_up
            splitter_result = self.splitter.run(documents=haystack_cleaned)
            chunked_documents = splitter_result["documents"]
            
            logger.info(f"After splitting: {len(chunked_documents)} document chunks created")
            
            # Step 4: Add chunk metadata
            for i, doc in enumerate(chunked_documents):
                if doc.meta is None:
                    doc.meta = {}
                
                doc.meta.update({
                    "chunk_id": i,
                    "chunk_size": len(doc.content),
                    "preprocessing_timestamp": self._get_timestamp()
                })
            
            logger.info(f"Successfully preprocessed {len(documents)} documents into {len(chunked_documents)} chunks")
            return chunked_documents
            
        except Exception as e:
            logger.error(f"Error during document preprocessing: {e}")
            raise Exception(f"Document preprocessing failed: {e}")
    
    def validate_documents(self, documents: List[Document]) -> List[Document]:
        """Validate and filter documents based on quality criteria.
        
        Args:
            documents: List of documents to validate.
            
        Returns:
            List of validated documents.
        """
        valid_documents = []
        
        for doc in documents:
            # Check minimum content length
            if len(doc.content.strip()) < 10:
                logger.debug(f"Skipping document with insufficient content: {len(doc.content)} characters")
                continue
            
            # Check for meaningful content (not just whitespace/punctuation)
            meaningful_chars = re.sub(r'[^\w]', '', doc.content)
            if len(meaningful_chars) < 5:
                logger.debug(f"Skipping document with no meaningful content")
                continue
            
            valid_documents.append(doc)
        
        logger.info(f"Validated {len(valid_documents)} out of {len(documents)} documents")
        return valid_documents
    
    def get_preprocessing_stats(self, original_docs: List[Document], processed_docs: List[Document]) -> dict:
        """Get statistics about the preprocessing operation.
        
        Args:
            original_docs: Original documents before preprocessing.
            processed_docs: Documents after preprocessing.
            
        Returns:
            Dictionary containing preprocessing statistics.
        """
        if not original_docs:
            return {"error": "No original documents provided"}
        
        original_total_chars = sum(len(doc.content) for doc in original_docs)
        processed_total_chars = sum(len(doc.content) for doc in processed_docs)
        
        return {
            "original_document_count": len(original_docs),
            "processed_chunk_count": len(processed_docs),
            "original_total_characters": original_total_chars,
            "processed_total_characters": processed_total_chars,
            "average_chunk_size": processed_total_chars / len(processed_docs) if processed_docs else 0,
            "compression_ratio": processed_total_chars / original_total_chars if original_total_chars > 0 else 0,
            "chunk_size_setting": self.chunk_size,
            "chunk_overlap_setting": self.chunk_overlap
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
