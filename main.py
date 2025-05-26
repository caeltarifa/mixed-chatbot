"""
Main entry point for the RAG application.
"""

import sys
import argparse
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from rag_app.services.rag_service import RAGService
from rag_app.utils.logger import get_logger, setup_logging
from rag_app.config.settings import settings

logger = get_logger(__name__)

def main():
    """Main function to run the RAG application."""
    parser = argparse.ArgumentParser(description="RAG Application with Haystack and Gemini")
    parser.add_argument("--index", action="store_true", help="Index PDF documents")
    parser.add_argument("--reindex", action="store_true", help="Force reindex all documents")
    parser.add_argument("--query", type=str, help="Query the RAG system")
    parser.add_argument("--interactive", action="store_true", help="Start interactive mode")
    parser.add_argument("--status", action="store_true", help="Show system status")
    parser.add_argument("--health", action="store_true", help="Perform health check")
    parser.add_argument("--summary", action="store_true", help="Generate document summary")
    parser.add_argument("--clear", action="store_true", help="Clear the document index")
    parser.add_argument("--log-level", type=str, default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    
    try:
        # Initialize RAG service
        logger.info("Initializing RAG Application...")
        rag_service = RAGService()
        
        # Handle different commands
        if args.status:
            show_status(rag_service)
        elif args.health:
            show_health_check(rag_service)
        elif args.clear:
            clear_index(rag_service)
        elif args.index or args.reindex:
            index_documents(rag_service, force_reindex=args.reindex)
        elif args.summary:
            show_summary(rag_service)
        elif args.query:
            query_system(rag_service, args.query)
        elif args.interactive:
            interactive_mode(rag_service)
        else:
            # Default behavior: show status and start interactive mode
            show_status(rag_service)
            print("\nStarting interactive mode...")
            interactive_mode(rag_service)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        print("\nGoodbye!")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def show_status(rag_service: RAGService):
    """Show system status."""
    print("=== RAG System Status ===")
    
    status = rag_service.get_status()
    
    print(f"Service Initialized: {status.get('service_initialized', False)}")
    print(f"Service Ready: {status.get('service_ready', False)}")
    print(f"Document Count: {status.get('document_count', 0)}")
    
    if 'indexing_status' in status:
        indexing = status['indexing_status']
        print(f"PDF Files Available: {indexing.get('total_pdf_files', 0)}")
        print(f"Index Status: {indexing.get('index_status', 'unknown')}")
    
    if 'store_info' in status:
        store = status['store_info']
        print(f"Database Path: {store.get('database_path', 'unknown')}")
        print(f"Database Size: {store.get('database_size_bytes', 0)} bytes")

def show_health_check(rag_service: RAGService):
    """Perform and show health check results."""
    print("=== Health Check ===")
    
    health = rag_service.health_check()
    
    print(f"Overall Health: {'✓ Healthy' if health.get('overall_healthy') else '✗ Unhealthy'}")
    
    if 'components' in health:
        print("\nComponent Status:")
        for component, status in health['components'].items():
            health_indicator = "✓" if status.get('healthy', False) else "✗"
            print(f"  {component}: {health_indicator} {'Healthy' if status.get('healthy', False) else 'Unhealthy'}")
            
            if 'error' in status:
                print(f"    Error: {status['error']}")

def clear_index(rag_service: RAGService):
    """Clear the document index."""
    print("=== Clearing Document Index ===")
    
    confirm = input("Are you sure you want to clear all indexed documents? (y/N): ")
    if confirm.lower() == 'y':
        result = rag_service.clear_index()
        
        if result['success']:
            print(f"✓ {result['message']}")
        else:
            print(f"✗ Error: {result.get('error', 'Unknown error')}")
    else:
        print("Operation cancelled.")

def index_documents(rag_service: RAGService, force_reindex: bool = False):
    """Index documents."""
    print("=== Indexing Documents ===")
    
    if force_reindex:
        print("Force reindexing all documents...")
    else:
        print("Indexing documents...")
    
    result = rag_service.index_documents(force_reindex=force_reindex)
    
    if result['success']:
        print(f"✓ {result['message']}")
        print(f"  Documents processed: {result.get('documents_processed', 0)}")
        print(f"  Chunks created: {result.get('chunks_created', 0)}")
        
        if 'chunks_with_embeddings' in result:
            print(f"  Chunks with embeddings: {result['chunks_with_embeddings']}")
    else:
        print(f"✗ Error: {result.get('error', 'Unknown error')}")

def show_summary(rag_service: RAGService):
    """Generate and show document summary."""
    print("=== Document Summary ===")
    
    if not rag_service.is_ready():
        print("No documents available. Please index documents first.")
        return
    
    print("Generating summary...")
    summary = rag_service.get_document_summary()
    
    print("\nSummary:")
    print("-" * 50)
    print(summary)
    print("-" * 50)

def query_system(rag_service: RAGService, query: str):
    """Query the RAG system."""
    print(f"=== Query: {query} ===")
    
    if not rag_service.is_ready():
        print("RAG system is not ready. Please index documents first.")
        return
    
    print("Processing query...")
    result = rag_service.query(query)
    
    print(f"\nQuestion: {result['question']}")
    print(f"Answer: {result['answer']}")
    
    if result.get('sources'):
        print(f"\nSources ({len(result['sources'])} documents):")
        for i, source in enumerate(result['sources'], 1):
            print(f"{i}. {source.get('file_name', 'Unknown file')}")
            if 'page_number' in source:
                print(f"   Page: {source['page_number']}")
            print(f"   Preview: {source['content_preview'][:100]}...")
            print()

def interactive_mode(rag_service: RAGService):
    """Start interactive query mode."""
    print("=== Interactive Mode ===")
    print("Enter your questions (type 'quit' to exit, 'help' for commands)")
    
    while True:
        try:
            user_input = input("\n🤖 Ask me anything: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            elif user_input.lower() == 'help':
                show_help()
                continue
            elif user_input.lower() == 'status':
                show_status(rag_service)
                continue
            elif user_input.lower() == 'index':
                index_documents(rag_service)
                continue
            elif user_input.lower() == 'summary':
                show_summary(rag_service)
                continue
            elif user_input.lower() == 'clear':
                clear_index(rag_service)
                continue
            
            # Process as query
            if rag_service.is_ready():
                result = rag_service.query(user_input)
                
                print(f"\n💡 Answer: {result['answer']}")
                
                if result.get('sources') and result['retrieved_documents'] > 0:
                    print(f"\n📚 Based on {result['retrieved_documents']} relevant documents")
                    
            else:
                print("⚠️  RAG system is not ready. Please run 'index' command first.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"Error: {e}")

def show_help():
    """Show help information."""
    print("""
Available commands:
  - Just type your question to query the system
  - 'status' - Show system status
  - 'index' - Index documents
  - 'summary' - Generate document summary
  - 'clear' - Clear document index
  - 'help' - Show this help
  - 'quit' or 'q' - Exit the application
    """)

if __name__ == "__main__":
    main()
