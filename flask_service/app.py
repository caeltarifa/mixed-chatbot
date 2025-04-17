import os
import logging
import json
import requests
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "physiotherapy-bot-secret")
CORS(app)

# Get Rasa API URL from environment or use default for local development
RASA_API_URL = os.environ.get("RASA_API_URL", "http://localhost:5005/webhooks/rest/webhook")

@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Process chat messages by sending them to Rasa server or using fallback responses."""
    try:
        # Get message from request
        user_message = request.json.get('message', '')
        
        if not user_message.strip():
            return jsonify([{"text": "Please enter a message."}])
        
        # Get or create a session ID
        sender_id = session.get("sender_id", None)
        if not sender_id:
            sender_id = os.urandom(16).hex()
            session["sender_id"] = sender_id
        
        logger.debug(f"Processing message from {sender_id}: {user_message}")
        
        # Use local fallback processing since Rasa isn't running
        return process_message_locally(user_message, sender_id)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify([{"text": "An unexpected error occurred. Please try again."}])

def process_message_locally(message, sender_id):
    """Process the message locally when Rasa server is not available."""
    message = message.lower()
    
    # Simple intent classification
    if any(greeting in message for greeting in ["hi", "hello", "hey", "greetings"]):
        return jsonify([{"text": "Hello! I'm your physiotherapy assistant. How can I help you today?"}])
    
    elif any(word in message for word in ["bye", "goodbye", "see you", "farewell"]):
        return jsonify([{"text": "Goodbye! Take care and remember to keep up with your exercises!"}])
    
    elif "thank" in message:
        return jsonify([{"text": "You're welcome! Is there anything else I can help you with?"}])
    
    # Body part detection
    body_parts = {
        "knee": ["knee", "knees"],
        "back": ["back", "spine", "lumbar", "spinal"],
        "shoulder": ["shoulder", "shoulders", "rotator cuff"],
        "neck": ["neck", "cervical"],
        "ankle": ["ankle", "ankles", "foot", "feet"],
        "hip": ["hip", "hips"],
        "elbow": ["elbow", "elbows"],
        "wrist": ["wrist", "wrists"],
        "hand": ["hand", "hands", "fingers"]
    }
    
    # Condition detection
    conditions = {
        "pain": ["pain", "ache", "hurts", "sore", "hurt", "hurting", "aching", "painful"],
        "stiffness": ["stiff", "stiffness", "rigid", "inflexible", "tight", "tightness"],
        "swelling": ["swelling", "swollen", "inflammation", "inflamed", "puffy"],
        "weakness": ["weak", "weakness", "fragile", "unstable", "wobbling"],
        "sprain": ["sprain", "strain", "twisted", "twist"],
        "injury": ["injury", "injured", "wound", "trauma", "hurt"]
    }
    
    # Extract body part and condition
    detected_body_part = None
    for part, keywords in body_parts.items():
        if any(keyword in message for keyword in keywords):
            detected_body_part = part
            break
    
    detected_condition = None
    for condition, keywords in conditions.items():
        if any(keyword in message for keyword in keywords):
            detected_condition = condition
            break
    
    # Generate appropriate response
    if detected_body_part and detected_condition:
        return jsonify([{"text": generate_exercise_recommendations(detected_body_part, detected_condition)}])
    elif detected_body_part:
        return jsonify([{"text": f"What specific issue are you experiencing with your {detected_body_part}? Is it pain, stiffness, swelling, or something else?"}])
    elif "exercise" in message or "recommendation" in message or "recommend" in message:
        return jsonify([{"text": "I'd be happy to recommend exercises! Please specify which body part you'd like exercises for (e.g., knee, back, shoulder)."}])
    elif "help" in message:
        return jsonify([{"text": "I can recommend exercises for different body parts and conditions. Just tell me which body part is bothering you and what symptoms you're experiencing."}])
    else:
        return jsonify([{"text": "I'm not sure I understand. Could you please specify which body part you need help with and what symptoms you're experiencing?"}])

def generate_exercise_recommendations(body_part, condition):
    """Generate exercise recommendations based on body part and condition."""
    exercises = {
        "knee": {
            "pain": "For knee pain, try these exercises:\n1. Straight Leg Raises: Lie on your back, keep one leg straight and the other bent. Raise the straight leg up to the height of the bent knee. Hold for 3 seconds, then lower. Repeat 10 times for 3 sets.\n2. Hamstring Stretches: Sit with one leg extended and the other bent. Reach toward your toes on the extended leg. Hold for 30 seconds. Repeat 3 times per leg.\n3. Wall Slides: Stand with your back against a wall, feet shoulder-width apart. Slide down until your knees are at about 45 degrees. Hold for 5-10 seconds, then slide back up.",
            "stiffness": "For knee stiffness, try these mobility exercises:\n1. Heel Slides: Lie on your back, slowly slide your heel toward your buttocks by bending your knee, then slide back to starting position. Repeat 10-15 times.\n2. Seated Knee Flexion and Extension: Sit on a chair, slowly extend one knee fully, hold for 5 seconds, then bend it back. Repeat 10 times for each leg.\n3. Stationary Bike: Use a stationary bike with minimal resistance for 5-10 minutes to improve knee mobility.",
            "swelling": "For knee swelling, try these gentle exercises:\n1. Ankle Pumps: Lie down with your leg elevated. Move your foot up and down at the ankle. Do 2-3 sets of 10 repetitions every hour.\n2. Quadriceps Sets: Sit with your leg extended, tighten the muscle on top of your thigh, hold for 5 seconds, then relax. Repeat 10 times, several times a day.\n3. Remember to use the RICE method: Rest, Ice, Compression, and Elevation to reduce swelling.",
            "weakness": "For knee weakness, try these strengthening exercises:\n1. Mini Squats: Stand holding onto a sturdy surface, bend knees to 30 degrees, hold for 3 seconds, then return to standing. Repeat 10 times for 3 sets.\n2. Step-Ups: Step up onto a small step with one foot, then the other. Step down in the same order. Start with a small step height and increase as strength improves.\n3. Resistance Band Exercises: Attach a resistance band around your ankles and perform side steps to strengthen the hip and thigh muscles that support the knee."
        },
        "back": {
            "pain": "For back pain, try these gentle exercises:\n1. Pelvic Tilts: Lie on your back with knees bent, feet flat. Tighten your stomach muscles and press your back into the floor. Hold for 5 seconds, then relax. Repeat 10 times.\n2. Cat-Cow Stretch: On hands and knees, arch your back up like a cat, then let it sag while lifting your head. Move slowly between positions 10 times.\n3. Partial Crunches: Lie on your back with knees bent, hands behind your head. Raise shoulders slightly off the floor, hold for 1 second, then lower. Repeat 8-12 times.",
            "stiffness": "For back stiffness, try these mobility exercises:\n1. Knee-to-Chest Stretches: Lie on your back, pull one knee to your chest, hold for 30 seconds. Alternate legs, repeat 3 times per leg.\n2. Rotation Stretches: Lie on your back, knees bent. Keeping shoulders on the floor, gently rotate your knees to one side, hold for 10 seconds, then rotate to the other side. Repeat 10 times each side.\n3. Child's Pose: Kneel on the floor, sit back on your heels, then stretch your arms forward and lower your torso. Hold for 30 seconds, repeat 3-5 times.",
            "injury": "For back injury recovery, consult with a healthcare provider before beginning these gentle exercises:\n1. Walking: Start with short, slow walks on level ground, gradually increasing duration.\n2. Wall Slides: Stand with back against wall, slowly slide down to a partial sitting position, hold for 5 seconds, then slide back up. Repeat 5-10 times.\n3. Gentle Swimming: If approved by your healthcare provider, swimming can provide low-impact movement for your back."
        },
        "shoulder": {
            "pain": "For shoulder pain, try these gentle exercises:\n1. Pendulum Swing: Lean forward supporting yourself with your good arm, let the affected arm hang down. Gently swing it in small circles, then back and forth. Do for 1-2 minutes.\n2. Cross-Body Reach: Use your good arm to gently pull the affected arm across your chest. Hold for 30 seconds, repeat 3 times.\n3. Doorway Stretch: Stand in a doorway with arms on the door frame at 90-degree angles, lean forward gently until you feel a stretch. Hold for 15-30 seconds.",
            "stiffness": "For shoulder stiffness, try these mobility exercises:\n1. Shoulder Rolls: Roll shoulders forward 10 times, then backward 10 times.\n2. Arm Slides Up Wall: Face a wall with your arm extended and hand flat against it. Slowly slide your arm upward as far as comfortable, then back down. Repeat 10 times.\n3. External Rotation: Hold a light weight or resistance band, elbow bent at 90 degrees at your side. Rotate forearm outward, keeping elbow tucked. Return slowly. Repeat 10 times for 3 sets."
        }
    }
    
    # Default message if specific combination not found
    default_message = f"I recommend consulting with a physiotherapist for specific exercises for your {body_part} {condition}. In the meantime, gentle movements within your pain-free range and proper rest can help."
    
    # Return specific exercises if available, otherwise return default
    try:
        return exercises[body_part][condition]
    except KeyError:
        # Check if we have any exercises for this body part
        if body_part in exercises:
            # Return exercises for any condition for this body part
            any_condition = next(iter(exercises[body_part]))
            return f"I don't have specific exercises for {body_part} {condition}, but here are some exercises that might help:\n\n{exercises[body_part][any_condition]}"
        return default_message

@app.route('/health_check', methods=['GET'])
def health_check():
    """Health check endpoint for the Flask service."""
    return jsonify({"status": "ok", "service": "flask"})

@app.route('/rasa_health_check', methods=['GET'])
def rasa_health_check():
    """Check if Rasa service is reachable."""
    try:
        response = requests.get(f"{RASA_API_URL.split('/webhooks')[0]}/status")
        if response.status_code == 200:
            return jsonify({"status": "ok", "service": "rasa"})
        else:
            return jsonify({"status": "error", "service": "rasa", "message": f"Status code: {response.status_code}"}), 500
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "service": "rasa", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)