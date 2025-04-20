import os
import logging
import requests
from flask import Flask, render_template, request, jsonify, session

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

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "physio-qa-secret-key")

# Initialize session with empty chat history
def initialize_session():
    if 'messages' not in session:
        session['messages'] = []

@app.route('/')
def index():
    # Initialize session if it doesn't exist
    initialize_session()
    return render_template('index.html', messages=session['messages'])

@app.route('/ask', methods=['POST'])
def ask_question():
    # Get question from form
    question = request.form.get('question', '').strip()
    
    if not question:
        return jsonify({
            'success': False,
            'error': 'Please enter a question'
        })
    
    # Add user message to chat history
    session['messages'].append({
        'role': 'user',
        'content': question
    })
    
    # Send request to backend API
    try:
        response = requests.post(
            f"{backend_url}/api/ask",
            json={
                'question': question,
                'top_k': 5
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            api_response = response.json()
            
            if api_response['success'] and api_response['answers']:
                best_answer = api_response['answers'][0]
                answer_content = best_answer['answer']
                context = best_answer.get('context', '')
                score = best_answer.get('score', 0)
                
                # Add assistant message to chat history
                session['messages'].append({
                    'role': 'assistant',
                    'content': answer_content,
                    'context': context,
                    'score': score
                })
                
                return jsonify({
                    'success': True,
                    'message': session['messages']
                })
            else:
                error_msg = api_response.get('error', 'No answer found')
                # Add error message to chat history
                session['messages'].append({
                    'role': 'assistant',
                    'content': f"I'm sorry, I couldn't find an answer to your question. {error_msg}",
                    'error': True
                })
                
                return jsonify({
                    'success': True,
                    'message': session['messages']
                })
        else:
            logger.error(f"API error: {response.status_code} - {response.text}")
            # Add error message to chat history
            session['messages'].append({
                'role': 'assistant',
                'content': f"I'm sorry, the API returned status code {response.status_code}.",
                'error': True
            })
            
            return jsonify({
                'success': False,
                'error': f"API returned status code {response.status_code}"
            })
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        # Add error message to chat history
        session['messages'].append({
            'role': 'assistant',
            'content': "I'm sorry, there was an error processing your question. Please try again later.",
            'error': True
        })
        
        return jsonify({
            'success': False,
            'error': f"Request failed: {str(e)}"
        })

@app.route('/health')
def health_check():
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            return jsonify({
                'frontend': 'healthy',
                'backend': response.json()
            })
        else:
            return jsonify({
                'frontend': 'healthy',
                'backend': 'unhealthy',
                'status_code': response.status_code
            })
    except requests.exceptions.RequestException as e:
        return jsonify({
            'frontend': 'healthy',
            'backend': 'unhealthy',
            'error': str(e)
        })

@app.route('/clear', methods=['POST'])
def clear_history():
    session['messages'] = []
    return jsonify({
        'success': True,
        'message': 'Chat history cleared'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
