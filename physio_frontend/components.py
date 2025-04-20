import streamlit as st
from typing import Dict, Any

def display_header():
    """Display the application header"""
    st.title("Physiotherapy Q&A Assistant 💪")
    st.markdown("""
    Welcome! Ask me any question about physiotherapy, and I'll provide
    information based on professional knowledge.
    """)
    st.markdown("---")

def render_chat_message(message: Dict[str, Any]):
    """
    Render a chat message in the UI
    
    Args:
        message: Message data including role, content, and optional metadata
    """
    role = message.get("role", "")
    content = message.get("content", "")
    
    if role == "user":
        # User message (question)
        with st.chat_message("user", avatar="🧑"):
            st.markdown(f"**Question**: {content}")
    
    elif role == "assistant":
        # Assistant message (answer)
        with st.chat_message("assistant", avatar="🤖"):
            if message.get("error", False):
                # Error message
                st.error(content)
            else:
                # Normal answer
                render_answer(message)

def render_answer(message: Dict[str, Any]):
    """
    Render an answer message with additional context
    
    Args:
        message: Answer message data
    """
    content = message.get("content", "")
    context = message.get("context", "")
    score = message.get("score", 0)
    
    # Main answer
    st.markdown(f"**Answer**: {content}")
    
    # Confidence and context in expandable section
    if context:
        with st.expander("See source context"):
            st.markdown(context)
            if score:
                confidence = int(score * 100)
                st.progress(min(score, 1.0), f"Confidence: {confidence}%")
