// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const typingIndicator = document.querySelector('.typing-indicator');
    
    // Function to add a message to the chat box
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Process markdown-like syntax for bold text
        let processedMessage = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Convert newlines to <br> tags
        processedMessage = processedMessage.replace(/\n/g, '<br>');
        
        contentDiv.innerHTML = processedMessage;
        messageDiv.appendChild(contentDiv);
        
        chatBox.appendChild(messageDiv);
        
        // Scroll to bottom of chat
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        typingIndicator.classList.remove('d-none');
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    // Function to hide typing indicator
    function hideTypingIndicator() {
        typingIndicator.classList.add('d-none');
    }
    
    // Function to handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (message) {
            // Add user message to chat
            addMessage(message, true);
            
            // Clear input field
            userInput.value = '';
            
            // Show typing indicator
            showTypingIndicator();
            
            // Send message to server
            sendMessageToServer(message);
        }
    });
    
    // Function to send message to server
    function sendMessageToServer(message) {
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Process response
            if (Array.isArray(data)) {
                data.forEach(item => {
                    if (item.text) {
                        addMessage(item.text);
                    }
                });
            } else if (data.text) {
                addMessage(data.text);
            } else {
                addMessage("I'm sorry, I didn't understand that. Could you rephrase?");
            }
        })
        .catch(error => {
            // Hide typing indicator
            hideTypingIndicator();
            
            console.error('Error:', error);
            addMessage("Sorry, there was an error processing your request. Please try again later.");
        });
    }
    
    // Function to handle example question clicks
    window.askExample = function(element) {
        const question = element.textContent.trim();
        userInput.value = question;
        chatForm.dispatchEvent(new Event('submit'));
    };
    
    // Focus input field on page load
    userInput.focus();
});
