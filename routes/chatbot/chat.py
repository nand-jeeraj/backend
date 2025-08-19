from flask import Blueprint, request, jsonify
from openai import OpenAI
import os
from datetime import datetime
from collections import defaultdict
from pymongo import MongoClient

router = Blueprint('chat', __name__)

# In-memory storage for chat histories (in production, use a database)
chat_histories = defaultdict(list)

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_chat_response(colid, message):
    """
    Get response from OpenAI API with conversation context
    """
    try:
        # Get previous messages for context
        previous_messages = [
            {"role": "system", "content": "You are a helpful college assistant. Keep responses concise and relevant to education."}
        ]
        
        # Add previous conversation history
        for msg in chat_histories[colid][-10:]:  # Keep last 10 messages for context
            previous_messages.append({
                "role": "user" if msg['sender'] == 'user' else "assistant",
                "content": msg['text']
            })
        
        # Add current message
        previous_messages.append({"role": "user", "content": message})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=previous_messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in OpenAI API call: {str(e)}")
        return "Sorry, I'm having trouble processing your request. Please try again later."

@router.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    colid = data.get('colid', 0)
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    # Add user message to history
    chat_histories[colid].append({
        'text': message,
        'sender': 'user',
        'timestamp': datetime.now().isoformat()
    })
    
    # Get bot response
    bot_response = get_chat_response(colid, message)
    
    # Add bot response to history
    chat_histories[colid].append({
        'text': bot_response,
        'sender': 'bot',
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({
        'reply': bot_response,
        'colid': colid
    })

@router.route('/chat/history', methods=['POST'])
def get_chat_history():
    data = request.get_json()
    colid = data.get('colid', 0)
    
    return jsonify({
        'messages': chat_histories.get(colid, []),
        'colid': colid
    })

@router.route('/chat/clear', methods=['POST'])
def clear_chat():
    data = request.get_json()
    colid = data.get('colid', 0)
    chat_histories[colid] = []  # Clear messages for this colid
    return jsonify({"success": True, "colid": colid})

@router.route('/quizzes', methods=['POST'])
def save_questions():
    try:
        data = request.get_json()
        colid = data.get('colid')
        questions = data.get('questions', [])
        quiz_type = data.get('type', 'quiz')
        
        # Connect to MongoDB
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("DB_NAME", "test")]
        
        # Save to appropriate collection
        if quiz_type == 'quiz':
            collection = db.quizzes
        else:
            collection = db.assignments
            
        result = collection.insert_one({
            'colid': colid,
            'questions': questions,
            'context': data.get('context', ''),
            'created_at': datetime.now(),
            'title': data.get('title', '')
        })

        return jsonify({
            'success': True,
            'inserted_id': str(result.inserted_id)
        })
        
    except Exception as e:
        print(f"Error saving questions: {str(e)}")
        return jsonify({"error": "Failed to save questions"}), 500