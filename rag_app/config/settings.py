"""
Application configuration settings.
"""

import os
from pathlib import Path
from typing import Optional

class Settings:
    """Application settings configuration."""
    
    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    RAG_APP_DIR: Path = BASE_DIR / "rag_app"
    DATA_DIR: Path = RAG_APP_DIR / "data_ingestion" / "raw_pdfs"
    
    # Database settings
    DATABASE_PATH: str = str(RAG_APP_DIR / "document_store" / "haystack_documents.db")
    
    # API settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "default_gemini_key")
    
    # Document processing settings
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # Embedding settings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # Retrieval settings
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Gemini model settings
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.3"))

    @classmethod
    def validate_settings(cls) -> bool:
        """Validate critical settings."""
        if cls.GEMINI_API_KEY == "default_gemini_key":
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        # Create necessary directories
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        (cls.RAG_APP_DIR / "document_store").mkdir(parents=True, exist_ok=True)
        
        return True

# Global settings instance
settings = Settings()
