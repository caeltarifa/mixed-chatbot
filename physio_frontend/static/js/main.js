document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const questionForm = document.getElementById('question-form');
    const questionInput = document.getElementById('question-input');
    const chatContainer = document.getElementById('chat-container');
    const clearChatButton = document.getElementById('clear-chat');
    const frontendStatus = document.querySelector('.frontend-status');
    const backendStatus = document.querySelector('.backend-status');

    // Set frontend status to healthy immediately
    frontendStatus.classList.add('healthy');

    // Check backend health status
    function checkHealth() {
        fetch('/health')
            .then(response => response.json())
            .then(data => {
                if (data.backend && data.backend.status === 'healthy') {
                    backendStatus.classList.add('healthy');
                } else {
                    backendStatus.classList.remove('healthy');
                }
            })
            .catch(error => {
                console.error('Health check failed:', error);
                backendStatus.classList.remove('healthy');
            });
    }

    // Initial health check
    checkHealth();
    // Check health every 30 seconds
    setInterval(checkHealth, 30000);

    // Handle form submission
    questionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const question = questionInput.value.trim();
        if (!question) return;

        // Add user message to UI immediately
        appendMessage('user', question);
        
        // Clear input field
        questionInput.value = '';
        
        // Show loading indicator
        const loadingMessage = appendMessage('assistant', '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div> Getting answer...');
        
        // Send question to backend
        const formData = new FormData();
        formData.append('question', question);
        
        fetch('/ask', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading message
            if (loadingMessage) {
                loadingMessage.remove();
            }
            
            // If successful and we have messages, update the chat with the latest assistant message
            if (data.success && data.message) {
                const messages = data.message;
                // Get the last assistant message
                const lastAssistantMessage = messages.filter(msg => msg.role === 'assistant').pop();
                if (lastAssistantMessage) {
                    appendAssistantMessage(lastAssistantMessage);
                }
            } else {
                // Show error
                appendMessage('assistant', `<div class="alert alert-danger">Error: ${data.error || 'Unknown error'}</div>`);
            }
        })
        .catch(error => {
            // Remove loading message
            if (loadingMessage) {
                loadingMessage.remove();
            }
            console.error('Error:', error);
            appendMessage('assistant', `<div class="alert alert-danger">Error: Unable to connect to server</div>`);
        });
    });

    // Clear chat history
    clearChatButton.addEventListener('click', function() {
        fetch('/clear', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                chatContainer.innerHTML = `
                    <div class="text-center text-muted py-5">
                        <i class="fas fa-comment-dots fa-3x mb-3"></i>
                        <p>No messages yet. Ask a question to get started!</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error clearing chat:', error);
        });
    });

    // Helper function to append messages to the chat
    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (role === 'user') {
            contentDiv.innerHTML = `<strong>Question:</strong> ${content}`;
        } else {
            contentDiv.innerHTML = content;
        }
        
        messageDiv.appendChild(contentDiv);
        
        // Clear 'no messages' placeholder if it exists
        const noMessages = chatContainer.querySelector('.text-center.text-muted.py-5');
        if (noMessages) {
            chatContainer.innerHTML = '';
        }
        
        chatContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return messageDiv;
    }

    // Helper function for assistant messages with additional context
    function appendAssistantMessage(message) {
        let content = '';
        
        if (message.error) {
            content = `<div class="alert alert-danger">${message.content}</div>`;
        } else {
            content = `<strong>Answer:</strong> ${message.content}`;
            
            // Add context if available
            if (message.context) {
                const contextId = `context-${Date.now()}`;
                content += `
                    <div class="context-container mt-2">
                        <a class="btn btn-sm btn-outline-secondary" data-bs-toggle="collapse" href="#${contextId}" role="button">
                            <i class="fas fa-file-alt"></i> View Source Context
                        </a>
                        <div class="collapse mt-2" id="${contextId}">
                            <div class="card card-body bg-light">
                                ${message.context}
                                ${message.score ? `
                                    <div class="progress mt-2" style="height: 5px;">
                                        <div class="progress-bar" role="progressbar" style="width: ${message.score * 100}%;" aria-valuenow="${message.score * 100}" aria-valuemin="0" aria-valuemax="100"></div>
                                    </div>
                                    <small class="text-muted">Confidence: ${Math.round(message.score * 100)}%</small>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }
        }
        
        return appendMessage('assistant', content);
    }
});