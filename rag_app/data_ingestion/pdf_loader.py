"""
PDF document loader for RAG application.
"""

import os
from typing import List, Optional
from pathlib import Path
import PyPDF2
from haystack import Document

from rag_app.utils.logger import get_logger
from rag_app.config.settings import settings

logger = get_logger(__name__)

class PDFLoader:
    """PDF document loader using PyPDF2."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize PDF loader.
        
        Args:
            data_dir: Directory containing PDF files. Defaults to settings.DATA_DIR.
        """
        self.data_dir = data_dir or settings.DATA_DIR
        logger.info(f"Initialized PDFLoader with data directory: {self.data_dir}")
    
    def load_pdf(self, file_path: Path) -> List[Document]:
        """Load a single PDF file and extract text.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            List of Haystack Document objects.
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist.
            Exception: If PDF parsing fails.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        logger.info(f"Loading PDF: {file_path}")
        documents = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if not pdf_reader.pages:
                    logger.warning(f"PDF file has no pages: {file_path}")
                    return documents
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        
                        if text.strip():  # Only create document if text is not empty
                            document = Document(
                                content=text.strip(),
                                meta={
                                    "source": str(file_path),
                                    "page_number": page_num,
                                    "file_name": file_path.name,
                                    "total_pages": len(pdf_reader.pages)
                                }
                            )
                            documents.append(document)
                            logger.debug(f"Extracted text from page {page_num}: {len(text)} characters")
                        else:
                            logger.warning(f"Page {page_num} has no extractable text")
                    
                    except Exception as e:
                        logger.error(f"Error extracting text from page {page_num}: {e}")
                        continue
                
                logger.info(f"Successfully loaded {len(documents)} documents from {file_path}")
                return documents
                
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")
            raise Exception(f"Failed to load PDF {file_path}: {e}")
    
    def load_all_pdfs(self) -> List[Document]:
        """Load all PDF files from the data directory.
        
        Returns:
            List of all loaded Haystack Document objects.
        """
        logger.info(f"Loading all PDFs from directory: {self.data_dir}")
        all_documents = []
        
        if not self.data_dir.exists():
            logger.warning(f"Data directory does not exist: {self.data_dir}")
            return all_documents
        
        pdf_files = list(self.data_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in directory: {self.data_dir}")
            return all_documents
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        for pdf_file in pdf_files:
            try:
                documents = self.load_pdf(pdf_file)
                all_documents.extend(documents)
            except Exception as e:
                logger.error(f"Failed to load PDF {pdf_file}: {e}")
                continue
        
        logger.info(f"Loaded total of {len(all_documents)} documents from {len(pdf_files)} PDF files")
        return all_documents
    
    def get_pdf_info(self, file_path: Path) -> dict:
        """Get metadata information about a PDF file.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Dictionary containing PDF metadata.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                info = {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                    "file_size": file_path.stat().st_size,
                    "page_count": len(pdf_reader.pages),
                    "metadata": {}
                }
                
                # Extract PDF metadata if available
                if pdf_reader.metadata:
                    for key, value in pdf_reader.metadata.items():
                        if value:
                            info["metadata"][key] = str(value)
                
                return info
                
        except Exception as e:
            logger.error(f"Error getting PDF info for {file_path}: {e}")
            raise Exception(f"Failed to get PDF info: {e}")
