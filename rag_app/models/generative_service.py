"""
Generative service using Google Gemini API.
"""

import os
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from haystack import Document

from rag_app.utils.logger import get_logger
from rag_app.config.settings import settings

logger = get_logger(__name__)

class GenerativeService:
    """Service for text generation using Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize generative service.
        
        Args:
            api_key: Gemini API key. If None, will use settings.GEMINI_API_KEY.
            model_name: Model name to use. If None, will use settings.GEMINI_MODEL.
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        
        if self.api_key == "default_gemini_key":
            raise ValueError("GEMINI_API_KEY must be set. Please set it in environment variables or .env file.")
        
        try:
            # Configure Gemini API
            genai.configure(api_key=self.api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel(self.model_name)
            
            # Test the connection
            self._test_connection()
            
            logger.info(f"Initialized GenerativeService with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error initializing generative service: {e}")
            raise Exception(f"Failed to initialize Gemini API: {e}")
    
    def _test_connection(self):
        """Test the Gemini API connection."""
        try:
            # Simple test query
            response = self.model.generate_content("Hello")
            if response and response.text:
                logger.debug("Gemini API connection test successful")
            else:
                raise Exception("No response from Gemini API")
                
        except Exception as e:
            logger.error(f"Gemini API connection test failed: {e}")
            raise Exception(f"Gemini API connection failed: {e}")
    
    def generate_response(
        self, 
        query: str, 
        context_documents: List[Document], 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate a response based on query and context documents.
        
        Args:
            query: User query.
            context_documents: List of relevant documents for context.
            max_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature for generation.
            
        Returns:
            Generated response text.
        """
        if not query or not query.strip():
            logger.warning("Empty query provided for response generation")
            return "I need a question to answer. Please provide a query."
        
        # Use default values if not provided
        max_tokens = max_tokens or settings.MAX_TOKENS
        temperature = temperature or settings.TEMPERATURE
        
        try:
            # Prepare context from documents
            context = self._prepare_context(context_documents)
            
            # Create the prompt
            prompt = self._create_rag_prompt(query, context)
            
            logger.debug(f"Generating response for query: '{query[:100]}...' with {len(context_documents)} context documents")
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if response and response.text:
                generated_text = response.text.strip()
                logger.info(f"Successfully generated response ({len(generated_text)} characters)")
                return generated_text
            else:
                logger.error("No text generated from Gemini API")
                return "I apologize, but I couldn't generate a response. Please try again."
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error while generating a response: {str(e)}"
    
    def _prepare_context(self, documents: List[Document]) -> str:
        """Prepare context text from documents.
        
        Args:
            documents: List of documents to use as context.
            
        Returns:
            Formatted context string.
        """
        if not documents:
            return "No relevant context available."
        
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            # Add document content
            content = doc.content.strip()
            
            # Add source information if available
            source_info = ""
            if doc.meta:
                if "source" in doc.meta:
                    source_info = f" (Source: {doc.meta['source']}"
                    if "page_number" in doc.meta:
                        source_info += f", Page {doc.meta['page_number']}"
                    source_info += ")"
            
            context_parts.append(f"Document {i}{source_info}:\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _create_rag_prompt(self, query: str, context: str) -> str:
        """Create a RAG prompt combining query and context.
        
        Args:
            query: User query.
            context: Context text from documents.
            
        Returns:
            Formatted prompt for the model.
        """
        prompt = f"""Based on the following context documents, please answer the user's question. If the answer cannot be found in the provided context, please say so clearly.

Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context provided. If you reference specific information, try to mention which document it came from.

Answer:"""
        
        return prompt
    
    def generate_summary(self, documents: List[Document]) -> str:
        """Generate a summary of the provided documents.
        
        Args:
            documents: List of documents to summarize.
            
        Returns:
            Generated summary text.
        """
        if not documents:
            return "No documents provided for summary."
        
        try:
            # Prepare content for summarization
            content_parts = []
            for doc in documents:
                content_parts.append(doc.content.strip())
            
            combined_content = "\n\n".join(content_parts)
            
            # Create summary prompt
            prompt = f"""Please provide a comprehensive summary of the following documents:

{combined_content}

Summary:"""
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return "Could not generate summary."
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def ask_question(self, question: str, documents: List[Document] = None) -> Dict[str, Any]:
        """Ask a question with optional document context.
        
        Args:
            question: Question to ask.
            documents: Optional list of documents for context.
            
        Returns:
            Dictionary containing response and metadata.
        """
        try:
            if documents:
                response = self.generate_response(question, documents)
                sources = self._extract_sources(documents)
            else:
                # Direct question without context
                response = self.model.generate_content(question)
                response_text = response.text if response and response.text else "No response generated."
                sources = []
                response = response_text
            
            return {
                "question": question,
                "answer": response,
                "sources": sources,
                "model": self.model_name,
                "has_context": bool(documents)
            }
            
        except Exception as e:
            logger.error(f"Error in ask_question: {e}")
            return {
                "question": question,
                "answer": f"Error: {str(e)}",
                "sources": [],
                "model": self.model_name,
                "has_context": False
            }
    
    def _extract_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Extract source information from documents.
        
        Args:
            documents: List of documents.
            
        Returns:
            List of source information dictionaries.
        """
        sources = []
        
        for doc in documents:
            if doc.meta:
                source_info = {
                    "content_preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                }
                
                # Add available metadata
                for key in ["source", "file_name", "page_number", "chunk_id"]:
                    if key in doc.meta:
                        source_info[key] = doc.meta[key]
                
                sources.append(source_info)
        
        return sources
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the generative model.
        
        Returns:
            Dictionary containing model information.
        """
        return {
            "model_name": self.model_name,
            "provider": "Google Gemini",
            "max_tokens": settings.MAX_TOKENS,
            "temperature": settings.TEMPERATURE,
            "api_configured": bool(self.api_key and self.api_key != "default_gemini_key")
        }
