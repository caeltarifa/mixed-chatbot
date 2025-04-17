from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# TODO: langchain API integration for dynamic exercise recommendations

# Dictionary of exercises by body part and condition
EXERCISES = {
    "back": {
        "pain": [
            {
                "name": "Pelvic Tilt",
                "instructions": "Lie on your back with knees bent. Flatten your back against the floor by tightening your abdominal muscles and bending your pelvis up slightly. Hold for 5 seconds and release. Repeat 10 times."
            },
            {
                "name": "Knee-to-Chest Stretch",
                "instructions": "Lie on your back with knees bent. Bring one knee to your chest, holding it with both hands for 15-30 seconds. Lower and repeat with the other leg. Do this 3 times for each leg."
            },
            {
                "name": "Cat-Cow Stretch",
                "instructions": "Start on your hands and knees. Arch your back upward (cat) and then let it sag (cow). Move slowly between positions 10 times."
            }
        ],
        "stiffness": [
            {
                "name": "Seated Spinal Twist",
                "instructions": "Sit with legs extended. Bend your right knee and place your foot outside your left thigh. Twist your torso to the right, holding for 20-30 seconds. Repeat on the other side."
            },
            {
                "name": "Child's Pose",
                "instructions": "Kneel with feet together, knees hip-width apart. Sit back on your heels and stretch arms forward, lowering your chest to the floor. Hold for 30 seconds."
            }
        ]
    },
    "neck": {
        "pain": [
            {
                "name": "Neck Rotation",
                "instructions": "Slowly turn your head to the right, hold for 15 seconds. Return to center, then turn to the left. Repeat 5 times on each side."
            },
            {
                "name": "Chin Tucks",
                "instructions": "Sit or stand with good posture. Gently tuck your chin in, keeping your head level. Hold for 5 seconds, repeat 10 times."
            }
        ],
        "stiffness": [
            {
                "name": "Neck Stretches",
                "instructions": "Tilt your head toward one shoulder until you feel a stretch. Hold for 15-30 seconds. Repeat on the other side. Do this 3 times per side."
            },
            {
                "name": "Shoulder Blade Squeeze",
                "instructions": "Sit or stand with arms at sides. Pull your shoulder blades together, hold for 5 seconds, then release. Repeat 10 times."
            }
        ]
    },
    "shoulder": {
        "pain": [
            {
                "name": "Pendulum Exercise",
                "instructions": "Lean forward supporting yourself with one hand. Let your affected arm hang down. Swing it gently in small circles, then back and forth. Do this for 1 minute."
            },
            {
                "name": "Shoulder External Rotation",
                "instructions": "Hold a light resistance band with elbows bent at 90 degrees. Pull the band outward, rotating at the shoulder. Hold 5 seconds, repeat 10 times."
            }
        ],
        "stiffness": [
            {
                "name": "Cross-Body Shoulder Stretch",
                "instructions": "Bring one arm across your chest, holding it with the other arm above the elbow. Hold for 30 seconds. Repeat on the other side."
            },
            {
                "name": "Wall Angels",
                "instructions": "Stand with back against a wall, arms in 'W' position. Slowly raise arms up the wall in a snow angel motion. Repeat 10 times."
            }
        ]
    },
    "knee": {
        "pain": [
            {
                "name": "Straight Leg Raises",
                "instructions": "Lie on your back with one knee bent, the other straight. Tighten the thigh of the straight leg and lift it to the height of the bent knee. Hold 5 seconds, lower slowly. Repeat 10 times."
            },
            {
                "name": "Hamstring Stretch",
                "instructions": "Sit with one leg extended, the other bent. Reach toward the toes of the extended leg, holding for 30 seconds. Repeat on the other side."
            }
        ],
        "stiffness": [
            {
                "name": "Knee Bends",
                "instructions": "Hold onto a chair for support. Slowly bend your knee as far as comfortable, then straighten. Repeat 10 times with each leg."
            },
            {
                "name": "Wall Slides",
                "instructions": "Stand with back against wall, feet shoulder-width apart. Slowly slide down into a partial squat, then back up. Repeat 10 times."
            }
        ]
    },
    "ankle": {
        "pain": [
            {
                "name": "Ankle Circles",
                "instructions": "Sit with your leg extended. Rotate your ankle 10 times clockwise, then 10 times counterclockwise. Repeat with the other ankle."
            },
            {
                "name": "Towel Stretch",
                "instructions": "Sit with legs extended. Loop a towel around your foot and gently pull toward you, feeling a stretch in your calf. Hold 30 seconds, repeat 3 times per foot."
            }
        ],
        "sprain": [
            {
                "name": "Alphabet Drawing",
                "instructions": "Using your foot, trace each letter of the alphabet in the air. This improves range of motion."
            },
            {
                "name": "Heel Raises",
                "instructions": "Stand with feet flat. Slowly rise onto toes, then lower. Use a chair for balance if needed. Repeat 15 times."
            }
        ]
    },
    "general": {
        "conditioning": [
            {
                "name": "Walking",
                "instructions": "Start with 10-15 minutes of walking at a comfortable pace. Gradually increase duration as tolerated."
            },
            {
                "name": "Chair Squats",
                "instructions": "Stand in front of a chair with feet shoulder-width apart. Lower yourself as if sitting down, but stop just before touching the chair. Return to standing. Repeat 10 times."
            },
            {
                "name": "Arm Circles",
                "instructions": "Stand with arms extended to sides. Make small circles forward for 30 seconds, then backward for 30 seconds."
            }
        ],
        "stretching": [
            {
                "name": "Full Body Stretch",
                "instructions": "Stand tall, reach arms overhead, and stretch upward. Hold for 10 seconds, release and repeat 3 times."
            },
            {
                "name": "Calf Stretch",
                "instructions": "Stand facing a wall with hands at eye level. Place one leg behind you, keeping heel down. Lean forward until you feel a stretch in your calf. Hold 30 seconds, switch legs."
            }
        ]
    }
}

class ActionRecommendExercises(Action):
    """Action to recommend exercises based on body part and condition."""
    
    def name(self) -> Text:
        return "action_recommend_exercises"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        body_part = tracker.get_slot("body_part")
        condition = tracker.get_slot("condition")
        
        # Default to general conditioning if specifics aren't available
        if not body_part:
            body_part = "general"
        if not condition:
            condition = "conditioning"
        
        # Look up appropriate exercises
        body_exercises = EXERCISES.get(body_part.lower(), EXERCISES["general"])
        condition_exercises = body_exercises.get(condition.lower(), body_exercises.get(list(body_exercises.keys())[0]))
        
        # Respond with exercise recommendations
        if condition_exercises:
            response = f"Here are some recommended exercises for {condition} in the {body_part}:\n\n"
            
            for i, exercise in enumerate(condition_exercises, 1):
                response += f"{i}. **{exercise['name']}**\n"
                response += f"   {exercise['instructions']}\n\n"
                
            response += "Always consult with a healthcare professional before starting any new exercise program, especially if you have existing health conditions."
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(text=f"I don't have specific exercises for {condition} in the {body_part}, but I recommend consulting with a physiotherapist for personalized guidance.")
        
        return []

class ActionAskBodyPart(Action):
    """Action to ask for body part if not provided."""
    
    def name(self) -> Text:
        return "action_ask_body_part"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="Which part of your body needs attention? For example: back, neck, shoulder, knee, or ankle?")
        return []

class ActionAskCondition(Action):
    """Action to ask for condition if not provided."""
    
    def name(self) -> Text:
        return "action_ask_condition"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        body_part = tracker.get_slot("body_part")
        
        if body_part:
            if body_part.lower() in EXERCISES:
                conditions = list(EXERCISES[body_part.lower()].keys())
                condition_text = ", ".join(conditions)
                dispatcher.utter_message(text=f"What's the issue with your {body_part}? Common conditions include: {condition_text}")
            else:
                dispatcher.utter_message(text=f"What's the issue with your {body_part}? For example: pain, stiffness, or injury?")
        else:
            dispatcher.utter_message(text="What's your condition? For example: pain, stiffness, injury, or general conditioning?")
        
        return []

class ActionProvideGeneralInfo(Action):
    """Action to provide general information about physiotherapy."""
    
    def name(self) -> Text:
        return "action_provide_general_info"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="""
        Physiotherapy, also called physical therapy, is a healthcare profession that helps people improve movement, manage pain, and prevent or recover from injuries or physical disabilities.
        
        Some key aspects of physiotherapy include:
        
        1. Exercise therapy - specific movements to improve strength, flexibility, and function
        2. Manual therapy - hands-on techniques to help relieve pain and stiffness
        3. Education - teaching you how to manage your condition and prevent future problems
        4. Movement analysis - identifying issues with how you move that might be causing problems
        
        Physiotherapists work with people of all ages, from newborns to elderly individuals, and can help with a wide range of conditions affecting the muscles, joints, bones, nervous system, heart, and lungs.
        
        I can recommend exercises for specific body parts and conditions, but always consult with a qualified physiotherapist for a proper diagnosis and personalized treatment plan.
        """)
        
        return []

class ActionResetSlots(Action):
    """Action to reset slots."""
    
    def name(self) -> Text:
        return "action_reset_slots"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        return [SlotSet("body_part", None), SlotSet("condition", None)]
