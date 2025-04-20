import os
import logging
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from data import load_documents, simple_search, PhysioDocument

# Configure logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Physiotherapy Q&A API",
    description="API for answering physiotherapy-related questions",
    version="1.0.0"
)

# Global variable to store documents
documents: List[PhysioDocument] = []

class QuestionRequest(BaseModel):
    question: str
    top_k: int = 5

class AnswerResponse(BaseModel):
    question: str
    answers: List[Dict[str, Any]]
    success: bool
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    global documents
    logger.info("Loading physiotherapy documents...")
    try:
        documents = load_documents()
        logger.info(f"Loaded {len(documents)} documents successfully")
    except Exception as e:
        logger.error(f"Failed to load documents: {str(e)}")
        documents = []

@app.get("/")
def read_root():
    return {"status": "Physiotherapy Q&A API is running"}

@app.get("/health")
def health_check():
    if documents:
        return {"status": "healthy", "documents_count": len(documents)}
    return {"status": "unhealthy", "documents_count": 0}

@app.post("/api/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    if not documents:
        logger.error("No documents loaded")
        raise HTTPException(
            status_code=503,
            detail="Service unavailable: No documents loaded"
        )
    
    try:
        logger.info(f"Processing question: {request.question}")
        search_results = simple_search(request.question, documents, request.top_k)
        
        # Format answers for response
        answers = []
        for result in search_results:
            answers.append({
                "answer": result["content"],
                "score": result["score"],
                "context": result["content"],
                "document_id": result["metadata"].get("paragraph_id", "unknown")
            })
        
        return {
            "question": request.question,
            "answers": answers,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        return {
            "question": request.question,
            "answers": [],
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
