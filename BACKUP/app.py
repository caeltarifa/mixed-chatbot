import os
import logging
import re
import json
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "physiotherapy-bot-secret")
CORS(app)

# Import exercise data from actions.py
from actions import EXERCISES

# Global user session state to track conversations
SESSIONS = {}

# Define intents and their patterns
INTENT_PATTERNS = {
    "greet": [
        r"^(hi|hello|hey|good morning|good evening|howdy)( there)?!?$"
    ],
    "goodbye": [
        r"^(bye|goodbye|see you|ttyl|talk to you later)!?$"
    ],
    "thanks": [
        r"^(thanks|thank you|thx|thank).*$"
    ],
    "bot_challenge": [
        r"^(are you a bot|are you human|who are you|what are you).*$"
    ],
    "ask_exercise": [
        r"exercise.* for (.*)",
        r"(what|recommend|suggest).* exercise.* (for|to) (.*)",
        r"help.* (with|for) .*(pain|ache|stiffness|injury|strain|sprain).*",
        r"(my|have|suffering|from) .*(pain|ache|stiffness|injury|strain|sprain).*",
        r"(what|how) .*(can|should) .*(i|one) do for .*(pain|ache|stiffness|injury).*",
        r".*strengthen.* (my|the) (.*)"
    ],
    "ask_physiotherapy_info": [
        r"^what is (physiotherapy|physical therapy).*$",
        r"^tell me about (physiotherapy|physical therapy).*$",
        r"^how (does|do) (physiotherapy|physical therapy) work.*$",
        r"^benefits of (physiotherapy|physical therapy).*$"
    ],
    "request_help": [
        r"^(help|help me|what can you do|how can you help|what can i ask).*$"
    ]
}

# Recognized body parts
BODY_PARTS = [
    "back", "neck", "shoulder", "knee", "ankle", "hip", "wrist", "elbow", 
    "foot", "leg", "arm", "hamstring", "calf", "quadricep", "lower back", "upper back"
]

# Recognized conditions
CONDITIONS = [
    "pain", "stiffness", "sprain", "strain", "weakness", "injury", 
    "rehabilitation", "recovery", "strengthening", "mobility", "flexibility"
]

# Standard responses
RESPONSES = {
    "greet": [
        "Hello! I'm your physiotherapy assistant. I can help you with exercises for different body parts and conditions. How can I help you today?"
    ],
    "goodbye": [
        "Goodbye! Take care and remember to do your exercises regularly."
    ],
    "thanks": [
        "You're welcome! Let me know if you need more help with your physiotherapy exercises."
    ],
    "bot_challenge": [
        "I am a physiotherapy assistance bot, designed to help you with rehabilitation exercises and information. While I can provide general guidance, I'm not a replacement for a qualified physiotherapist."
    ],
    "request_help": [
        "I can help you with physiotherapy exercises and information. You can ask me for exercises for specific body parts like 'back', 'knee', or 'shoulder', or ask about conditions like 'pain' or 'stiffness'. For example, try asking 'What exercises help with back pain?' or 'Give me some shoulder exercises'."
    ],
    "default": [
        "I'm sorry, I didn't quite understand that. Could you rephrase or ask me about specific exercises for a body part, like your back, knee, or shoulder?"
    ]
}

def extract_entities(message: str) -> Dict[str, str]:
    """Extract body part and condition entities from the message."""
    entities = {}
    
    # Look for body parts
    for part in BODY_PARTS:
        if re.search(r'\b' + part + r'\b', message.lower()):
            entities["body_part"] = part
            break
    
    # Look for conditions
    for condition in CONDITIONS:
        if re.search(r'\b' + condition + r'\b', message.lower()):
            entities["condition"] = condition
            break
    
    return entities

def detect_intent(message: str) -> Dict[str, Any]:
    """Detect the intent and entities in the user message."""
    result = {
        "intent": None,
        "entities": {}
    }
    
    # Check each intent pattern
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message.lower()):
                result["intent"] = intent
                break
        if result["intent"]:
            break
    
    # If no intent matched, use default
    if not result["intent"]:
        result["intent"] = "default"
    
    # Extract entities if it's an ask_exercise intent
    if result["intent"] == "ask_exercise" or result["intent"] == "default":
        result["entities"] = extract_entities(message)
    
    return result

def recommend_exercises(body_part: Optional[str] = None, condition: Optional[str] = None) -> str:
    """Generate exercise recommendations based on body part and condition."""
    # Default to general conditioning if specifics aren't available
    if not body_part:
        body_part = "general"
    if not condition:
        condition = "conditioning" if body_part == "general" else list(EXERCISES.get(body_part.lower(), EXERCISES["general"]).keys())[0]
    
    # Look up appropriate exercises
    body_exercises = EXERCISES.get(body_part.lower(), EXERCISES["general"])
    condition_exercises = body_exercises.get(condition.lower(), body_exercises.get(list(body_exercises.keys())[0]))
    
    # Generate response
    if condition_exercises:
        response = f"Here are some recommended exercises for {condition} in the {body_part}:\n\n"
        
        for i, exercise in enumerate(condition_exercises, 1):
            response += f"{i}. **{exercise['name']}**\n"
            response += f"   {exercise['instructions']}\n\n"
            
        response += "Always consult with a healthcare professional before starting any new exercise program, especially if you have existing health conditions."
    else:
        response = f"I don't have specific exercises for {condition} in the {body_part}, but I recommend consulting with a physiotherapist for personalized guidance."
    
    return response

def provide_general_info() -> str:
    """Provide general information about physiotherapy."""
    return """
Physiotherapy, also called physical therapy, is a healthcare profession that helps people improve movement, manage pain, and prevent or recover from injuries or physical disabilities.

Some key aspects of physiotherapy include:

1. Exercise therapy - specific movements to improve strength, flexibility, and function
2. Manual therapy - hands-on techniques to help relieve pain and stiffness
3. Education - teaching you how to manage your condition and prevent future problems
4. Movement analysis - identifying issues with how you move that might be causing problems

Physiotherapists work with people of all ages, from newborns to elderly individuals, and can help with a wide range of conditions affecting the muscles, joints, bones, nervous system, heart, and lungs.

I can recommend exercises for specific body parts and conditions, but always consult with a qualified physiotherapist for a proper diagnosis and personalized treatment plan.
"""

def ask_body_part() -> str:
    """Ask for body part if not provided."""
    return "Which part of your body needs attention? For example: back, neck, shoulder, knee, or ankle?"

def ask_condition(body_part: Optional[str] = None) -> str:
    """Ask for condition if not provided."""
    if body_part and body_part.lower() in EXERCISES:
        conditions = list(EXERCISES[body_part.lower()].keys())
        condition_text = ", ".join(conditions)
        return f"What's the issue with your {body_part}? Common conditions include: {condition_text}"
    else:
        return "What's your condition? For example: pain, stiffness, injury, or general conditioning?"

def get_response(sender_id: str, message: str) -> List[Dict[str, str]]:
    """Generate a response based on the user's message."""
    # Initialize session if it doesn't exist
    if sender_id not in SESSIONS:
        SESSIONS[sender_id] = {
            "last_intent": None,
            "body_part": None,
            "condition": None,
            "awaiting": None
        }
    
    session = SESSIONS[sender_id]
    
    # Parse the message to determine intent and entities
    parsed = detect_intent(message)
    logger.debug(f"Parsed message: {parsed}")
    
    intent = parsed["intent"]
    entities = parsed["entities"]
    
    # Update session with any entities found
    if "body_part" in entities:
        session["body_part"] = entities["body_part"]
    if "condition" in entities:
        session["condition"] = entities["condition"]
    
    responses = []
    
    # Handle awaiting states
    if session["awaiting"] == "body_part" and "body_part" in entities:
        session["awaiting"] = "condition"
        responses.append({"text": ask_condition(session["body_part"])})
        return responses
    elif session["awaiting"] == "condition" and "condition" in entities:
        session["awaiting"] = None
        responses.append({"text": recommend_exercises(session["body_part"], session["condition"])})
        # Reset slots after providing exercises
        session["body_part"] = None
        session["condition"] = None
        return responses
    
    # Generate response based on intent
    if intent == "greet":
        responses.append({"text": RESPONSES["greet"][0]})
    
    elif intent == "goodbye":
        responses.append({"text": RESPONSES["goodbye"][0]})
    
    elif intent == "thanks":
        responses.append({"text": RESPONSES["thanks"][0]})
    
    elif intent == "bot_challenge":
        responses.append({"text": RESPONSES["bot_challenge"][0]})
    
    elif intent == "request_help":
        responses.append({"text": RESPONSES["request_help"][0]})
    
    elif intent == "ask_physiotherapy_info":
        responses.append({"text": provide_general_info()})
    
    elif intent == "ask_exercise":
        if session["body_part"] and session["condition"]:
            responses.append({"text": recommend_exercises(session["body_part"], session["condition"])})
            # Reset slots after providing exercises
            session["body_part"] = None
            session["condition"] = None
        elif session["body_part"]:
            session["awaiting"] = "condition"
            responses.append({"text": ask_condition(session["body_part"])})
        elif "body_part" in entities:
            session["body_part"] = entities["body_part"]
            session["awaiting"] = "condition"
            responses.append({"text": ask_condition(session["body_part"])})
        else:
            session["awaiting"] = "body_part"
            responses.append({"text": ask_body_part()})
    
    else:  # default intent
        if "body_part" in entities or "condition" in entities:
            # Treat as an exercise request if entities are found
            if session["body_part"] and session["condition"]:
                responses.append({"text": recommend_exercises(session["body_part"], session["condition"])})
                # Reset slots after providing exercises
                session["body_part"] = None
                session["condition"] = None
            elif session["body_part"]:
                session["awaiting"] = "condition"
                responses.append({"text": ask_condition(session["body_part"])})
            elif "body_part" in entities:
                session["body_part"] = entities["body_part"]
                session["awaiting"] = "condition"
                responses.append({"text": ask_condition(session["body_part"])})
            else:
                session["awaiting"] = "body_part"
                responses.append({"text": ask_body_part()})
        else:
            responses.append({"text": RESPONSES["default"][0]})
    
    # Update last intent
    session["last_intent"] = intent
    
    return responses

@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Process chat messages and generate responses."""
    try:
        # Get message from request
        user_message = request.json.get('message', '')
        
        if not user_message.strip():
            return jsonify({"text": "Please enter a message."})
        
        # Get or create a session ID
        sender_id = session.get("sender_id", None)
        if not sender_id:
            sender_id = os.urandom(16).hex()
            session["sender_id"] = sender_id
        
        logger.debug(f"Processing message from {sender_id}: {user_message}")
        
        # Generate response
        responses = get_response(sender_id, user_message)
        
        return jsonify(responses)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify([{"text": "An unexpected error occurred. Please try again."}])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
