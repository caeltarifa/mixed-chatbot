"""
Logging utility for RAG application.
"""

import logging
import sys
from typing import Optional
from pathlib import Path

from rag_app.config.settings import settings

def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> None:
    """Setup logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional file path for log output.
        console_output: Whether to output logs to console.
    """
    log_level = log_level or settings.LOG_LEVEL
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
    
    # Set up specific loggers to reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("haystack").setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.
    
    Args:
        name: Logger name (typically __name__ of the module).
        
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)

def log_function_call(func):
    """Decorator to log function calls with arguments and return values.
    
    Args:
        func: Function to decorate.
        
    Returns:
        Decorated function.
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # Log function entry
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    
    return wrapper

def log_execution_time(func):
    """Decorator to log function execution time.
    
    Args:
        func: Function to decorate.
        
    Returns:
        Decorated function.
    """
    import time
    
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {e}")
            raise
    
    return wrapper

class ContextLogger:
    """Context manager for structured logging with additional context."""
    
    def __init__(self, logger: logging.Logger, context: str, level: int = logging.INFO):
        """Initialize context logger.
        
        Args:
            logger: Logger instance to use.
            context: Context description.
            level: Logging level.
        """
        self.logger = logger
        self.context = context
        self.level = level
        self.start_time = None
    
    def __enter__(self):
        """Enter the context."""
        self.start_time = self._get_timestamp()
        self.logger.log(self.level, f"Starting {self.context}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        end_time = self._get_timestamp()
        
        if exc_type is None:
            self.logger.log(self.level, f"Completed {self.context}")
        else:
            self.logger.error(f"Failed {self.context}: {exc_val}")
        
        return False  # Don't suppress exceptions
    
    def log(self, message: str, level: Optional[int] = None):
        """Log a message within this context.
        
        Args:
            message: Message to log.
            level: Optional logging level override.
        """
        log_level = level or self.level
        self.logger.log(log_level, f"[{self.context}] {message}")
    
    def _get_timestamp(self):
        """Get current timestamp."""
        import time
        return time.time()

def create_file_logger(name: str, log_file: Path, level: str = "INFO") -> logging.Logger:
    """Create a dedicated file logger.
    
    Args:
        name: Logger name.
        log_file: Path to log file.
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # Create file handler
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file logger: {e}")
    
    return logger

# Initialize logging when module is imported
setup_logging()
