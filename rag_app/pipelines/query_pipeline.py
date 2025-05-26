"""
Query pipeline for RAG application.
"""

from typing import List, Dict, Any, Optional
from haystack import Document, Pipeline
from haystack.components.retrievers import InMemoryEmbeddingRetriever

from rag_app.models.embedding_service import EmbeddingService
from rag_app.models.generative_service import GenerativeService
from rag_app.document_store.local_document_store import LocalDocumentStore
from rag_app.utils.logger import get_logger
from rag_app.config.settings import settings

logger = get_logger(__name__)

class QueryPipeline:
    """Pipeline for querying documents and generating responses."""
    
    def __init__(
        self, 
        document_store: Optional[LocalDocumentStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        generative_service: Optional[GenerativeService] = None
    ):
        """Initialize query pipeline.
        
        Args:
            document_store: Document store instance.
            embedding_service: Embedding service instance.
            generative_service: Generative service instance.
        """
        self.document_store = document_store or LocalDocumentStore()
        self.embedding_service = embedding_service or EmbeddingService()
        self.generative_service = generative_service or GenerativeService()
        
        # Sync document stores to ensure vector store has embeddings
        self.document_store.sync_stores()
        
        # Initialize retriever
        self._init_retriever()
        
        logger.info("Initialized QueryPipeline")
    
    def _init_retriever(self):
        """Initialize the document retriever."""
        try:
            # Use the vector store from document store
            self.retriever = InMemoryEmbeddingRetriever(
                document_store=self.document_store.vector_store,
                top_k=settings.TOP_K
            )
            
            logger.debug("Document retriever initialized")
            
        except Exception as e:
            logger.error(f"Error initializing retriever: {e}")
            self.retriever = None
    
    def query(self, question: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """Process a query and return response with sources.
        
        Args:
            question: User question.
            top_k: Number of top documents to retrieve.
            
        Returns:
            Dictionary containing answer, sources, and metadata.
        """
        if not question or not question.strip():
            logger.warning("Empty question provided")
            return {
                "question": question,
                "answer": "Please provide a valid question.",
                "sources": [],
                "retrieved_documents": 0,
                "success": False
            }
        
        top_k = top_k or settings.TOP_K
        
        logger.info(f"Processing query: '{question[:100]}...'")
        
        try:
            # Step 1: Retrieve relevant documents
            relevant_docs = self.retrieve_documents(question, top_k)
            
            if not relevant_docs:
                logger.warning("No relevant documents found for query")
                return {
                    "question": question,
                    "answer": "I couldn't find any relevant information to answer your question. Please try rephrasing your query or check if documents have been indexed.",
                    "sources": [],
                    "retrieved_documents": 0,
                    "success": False
                }
            
            # Step 2: Generate response using retrieved documents
            answer = self.generative_service.generate_response(question, relevant_docs)
            
            # Step 3: Extract source information
            sources = self._extract_source_info(relevant_docs)
            
            logger.info(f"Successfully processed query with {len(relevant_docs)} relevant documents")
            
            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "retrieved_documents": len(relevant_docs),
                "success": True,
                "model_info": self.generative_service.get_model_info()
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "question": question,
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "retrieved_documents": 0,
                "success": False,
                "error": str(e)
            }
    
    def retrieve_documents(self, query: str, top_k: int = None) -> List[Document]:
        """Retrieve relevant documents for a query.
        
        Args:
            query: Search query.
            top_k: Number of documents to retrieve.
            
        Returns:
            List of relevant documents.
        """
        top_k = top_k or settings.TOP_K
        
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_service.embed_text(query)
            
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Use retriever if available
            if self.retriever:
                try:
                    retriever_result = self.retriever.run(
                        query_embedding=query_embedding,
                        top_k=top_k
                    )
                    
                    if retriever_result and "documents" in retriever_result:
                        documents = retriever_result["documents"]
                        logger.debug(f"Retrieved {len(documents)} documents using Haystack retriever")
                        return documents
                    
                except Exception as e:
                    logger.warning(f"Haystack retriever failed, using fallback: {e}")
            
            # Fallback: Manual similarity search
            return self._manual_similarity_search(query_embedding, top_k)
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def _manual_similarity_search(self, query_embedding: List[float], top_k: int) -> List[Document]:
        """Perform manual similarity search as fallback.
        
        Args:
            query_embedding: Query embedding vector.
            top_k: Number of documents to retrieve.
            
        Returns:
            List of most similar documents.
        """
        try:
            # Get all documents
            all_docs = self.document_store.get_all_documents()
            
            if not all_docs:
                logger.warning("No documents available for similarity search")
                return []
            
            # Filter documents that have embeddings
            docs_with_embeddings = []
            document_embeddings = []
            
            for doc in all_docs:
                if hasattr(doc, 'embedding') and doc.embedding:
                    docs_with_embeddings.append(doc)
                    document_embeddings.append(doc.embedding)
            
            if not docs_with_embeddings:
                logger.warning("No documents with embeddings found")
                return []
            
            # Perform similarity search
            similar_indices = self.embedding_service.similarity_search(
                query_embedding, 
                document_embeddings, 
                top_k
            )
            
            # Return the most similar documents
            similar_docs = [docs_with_embeddings[i] for i in similar_indices if i < len(docs_with_embeddings)]
            
            logger.debug(f"Manual similarity search returned {len(similar_docs)} documents")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error in manual similarity search: {e}")
            return []
    
    def _extract_source_info(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Extract source information from documents.
        
        Args:
            documents: List of documents.
            
        Returns:
            List of source information dictionaries.
        """
        sources = []
        
        for i, doc in enumerate(documents):
            source_info = {
                "rank": i + 1,
                "content_preview": doc.content[:300] + "..." if len(doc.content) > 300 else doc.content,
                "content_length": len(doc.content)
            }
            
            # Add metadata if available
            if doc.meta:
                for key in ["source", "file_name", "page_number", "chunk_id"]:
                    if key in doc.meta:
                        source_info[key] = doc.meta[key]
            
            sources.append(source_info)
        
        return sources
    
    def ask_without_context(self, question: str) -> Dict[str, Any]:
        """Ask a question without document context (direct LLM query).
        
        Args:
            question: Question to ask.
            
        Returns:
            Dictionary containing response and metadata.
        """
        logger.info(f"Processing direct question (no context): '{question[:100]}...'")
        
        try:
            result = self.generative_service.ask_question(question)
            result["context_used"] = False
            result["success"] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing direct question: {e}")
            return {
                "question": question,
                "answer": f"Error: {str(e)}",
                "context_used": False,
                "success": False,
                "error": str(e)
            }
    
    def get_document_summary(self, document_filter: Optional[Dict[str, Any]] = None) -> str:
        """Get a summary of documents in the store.
        
        Args:
            document_filter: Optional filter criteria for documents.
            
        Returns:
            Generated summary text.
        """
        try:
            # Get documents based on filter
            if document_filter:
                documents = self.document_store.filter_documents(document_filter)
            else:
                documents = self.document_store.get_all_documents()
            
            if not documents:
                return "No documents available for summarization."
            
            # Limit number of documents for summarization to avoid token limits
            max_docs_for_summary = 10
            docs_to_summarize = documents[:max_docs_for_summary]
            
            summary = self.generative_service.generate_summary(docs_to_summarize)
            
            if len(documents) > max_docs_for_summary:
                summary += f"\n\nNote: This summary is based on {max_docs_for_summary} out of {len(documents)} total documents."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating document summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def search_documents(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search documents and return detailed results without generating an answer.
        
        Args:
            query: Search query.
            top_k: Number of results to return.
            
        Returns:
            List of search result dictionaries.
        """
        top_k = top_k or settings.TOP_K
        
        try:
            # Retrieve documents
            relevant_docs = self.retrieve_documents(query, top_k)
            
            # Format results
            results = []
            for i, doc in enumerate(relevant_docs):
                result = {
                    "rank": i + 1,
                    "content": doc.content,
                    "content_length": len(doc.content),
                    "metadata": doc.meta if doc.meta else {}
                }
                results.append(result)
            
            logger.info(f"Search returned {len(results)} results for query: '{query[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and configuration.
        
        Returns:
            Dictionary containing pipeline status information.
        """
        try:
            store_info = self.document_store.get_store_info()
            
            return {
                "document_store": store_info,
                "embedding_service": self.embedding_service.get_model_info(),
                "generative_service": self.generative_service.get_model_info(),
                "retriever_available": self.retriever is not None,
                "top_k_setting": settings.TOP_K,
                "pipeline_ready": store_info.get("total_documents", 0) > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {
                "error": str(e),
                "pipeline_ready": False
            }
