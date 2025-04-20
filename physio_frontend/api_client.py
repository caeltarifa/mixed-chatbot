import json
import logging
import requests
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PhysioQAClient:
    """Client for interacting with the Physiotherapy Q&A API"""
    
    def __init__(self, base_url: str):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        logger.info(f"Initialized API client with base URL: {self.base_url}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the API
        
        Returns:
            Dict with health status information
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}
    
    def ask_question(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Send a question to the API and get answers
        
        Args:
            question: The question to ask
            top_k: Number of answers to retrieve
            
        Returns:
            Dict with question, answers, and success status
        """
        logger.info(f"Asking question: {question}")
        
        try:
            payload = {
                "question": question,
                "top_k": top_k
            }
            
            response = self.session.post(
                f"{self.base_url}/api/ask",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {
                    "question": question,
                    "answers": [],
                    "success": False,
                    "error": f"API returned status code {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {
                "question": question,
                "answers": [],
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {str(e)}")
            return {
                "question": question,
                "answers": [],
                "success": False,
                "error": f"Failed to parse response: {str(e)}"
            }
