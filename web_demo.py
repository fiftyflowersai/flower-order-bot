#!/usr/bin/env python3
"""
Simple web demo for the flower chatbot
"""
from flask import Flask, render_template, request, jsonify, make_response
from v6_chat_bot import FlowerConsultant
import os

app = Flask(__name__)

# Store chatbot instances per session (simplified - in production use proper session management)
chatbots = {}

def get_chatbot(session_id="demo"):
    """Get or create chatbot instance"""
    if session_id not in chatbots:
        chatbots[session_id] = FlowerConsultant(debug=False)  # No debug output for web UI
    return chatbots[session_id]

@app.route('/')
def index():
    """Render the chat interface"""
    response = make_response(render_template('chat.html'))
    # Add header to skip ngrok warning page
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data.get('message', '')
    session_id = data.get('session_id', 'demo')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Get chatbot instance
    bot = get_chatbot(session_id)
    
    # Get response
    import io
    import sys
    
    # Capture the output
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    
    try:
        bot.ask(user_message)
        response = buffer.getvalue()
    finally:
        sys.stdout = old_stdout
    
    # Get current memory state
    memory_state = bot.memory.to_dict()
    
    # Filter out empty values for display
    active_filters = {k: v for k, v in memory_state.items() 
                     if v and v != [] and v != {'min': None, 'max': None, 'around': None}}
    
    return jsonify({
        'response': response,
        'memory': active_filters,
        'session_id': session_id
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the chatbot session"""
    data = request.json
    session_id = data.get('session_id', 'demo')
    
    if session_id in chatbots:
        del chatbots[session_id]
    
    return jsonify({'status': 'success', 'message': 'Chat session reset'})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("🌸 FiftyFlowers Chatbot Demo")
    print("=" * 60)
    print("Starting web server...")
    print("Open your browser to: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, port=5000)
