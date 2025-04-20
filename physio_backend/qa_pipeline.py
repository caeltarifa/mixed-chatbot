import os
import logging
from typing import Dict, List, Any

from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import FARMReader, BM25Retriever
from haystack.pipelines import ExtractiveQAPipeline

from document_store import initialize_document_store

# Configure logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def initialize_qa_pipeline():
    """
    Initialize the question answering pipeline with Haystack components
    
    Returns:
        ExtractiveQAPipeline: The initialized pipeline
    """
    logger.info("Initializing document store...")
    document_store = initialize_document_store()
    
    logger.info("Creating retriever...")
    retriever = BM25Retriever(document_store=document_store)
    
    logger.info("Creating reader...")
    # Using a smaller model for faster inference
    reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=False)
    
    logger.info("Creating pipeline...")
    pipe = ExtractiveQAPipeline(reader, retriever)
    
    return pipe

def get_answer(pipeline: ExtractiveQAPipeline, question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Get answers for the given question using the QA pipeline
    
    Args:
        pipeline: The QA pipeline
        question: The question to answer
        top_k: Number of answers to return
        
    Returns:
        List of answer dictionaries
    """
    logger.info(f"Getting answer for question: {question}")
    
    # Run the pipeline
    result = pipeline.run(
        query=question,
        params={
            "Retriever": {"top_k": top_k},
            "Reader": {"top_k": top_k}
        }
    )
    
    # Extract and format answers
    answers = []
    if "answers" in result:
        for answer in result["answers"]:
            answers.append({
                "answer": answer.answer,
                "score": float(answer.score),  # Convert to float for JSON serialization
                "context": answer.context,
                "document_id": answer.document_id
            })
    
    return answers
