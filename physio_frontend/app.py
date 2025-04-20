import streamlit as st
import logging
import os
from api_client import PhysioQAClient
from components import render_chat_message, render_answer, display_header

# Configure logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get backend URL from environment or use default
# In Replit, the Backend Service is accessible at localhost:8000
backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
logger.info(f"Using backend URL: {backend_url}")

# Initialize API client
api_client = PhysioQAClient(base_url=backend_url)

# Add a debug message to help troubleshoot
try:
    health_status = api_client.health_check()
    logger.info(f"Backend health check: {health_status}")
except Exception as e:
    logger.error(f"Failed to connect to backend: {str(e)}")

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "question" not in st.session_state:
        st.session_state.question = ""

def handle_question_submission():
    """Handle the submission of a question"""
    question = st.session_state.question.strip()
    
    if not question:
        st.warning("Please enter a question")
        return
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": question})
    
    # Clear input
    st.session_state.question = ""
    
    # Call API to get answer
    with st.spinner("Getting answer..."):
        try:
            response = api_client.ask_question(question)
            
            if response["success"] and response["answers"]:
                best_answer = response["answers"][0]
                answer_content = best_answer["answer"]
                context = best_answer["context"]
                score = best_answer["score"]
                
                # Add system message with answer
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer_content,
                    "context": context,
                    "score": score
                })
            else:
                error_msg = response.get("error", "No answer found")
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"I'm sorry, I couldn't find an answer to your question. {error_msg}",
                    "error": True
                })
        except Exception as e:
            logger.error(f"Error getting answer: {str(e)}")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "I'm sorry, there was an error processing your question. Please try again later.",
                "error": True
            })

def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Physiotherapy Q&A Assistant",
        page_icon="💪",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Display chat messages
    for message in st.session_state.messages:
        render_chat_message(message)
    
    # Input for new question
    st.text_input(
        "Ask a question about physiotherapy:",
        key="question",
        on_change=handle_question_submission,
        placeholder="e.g., What exercises help with lower back pain?"
    )
    
    # Health check for backend service
    try:
        health = api_client.health_check()
        if health.get("status") != "healthy":
            st.sidebar.warning("⚠️ Backend service health check failed")
        else:
            st.sidebar.success("✅ Backend service is healthy")
    except Exception as e:
        st.sidebar.error(f"❌ Backend service unavailable: {str(e)}")
    
    # Instructions in sidebar
    st.sidebar.title("About")
    st.sidebar.info(
        """
        This application uses natural language processing to answer questions 
        about physiotherapy. Ask about:
        
        - Treatment techniques
        - Exercises for specific conditions
        - Rehabilitation protocols
        - Pain management strategies
        - General physiotherapy knowledge
        """
    )

if __name__ == "__main__":
    main()
