import os
from google import genai
from google.genai import types

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from services import chat_bot

# APIs
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)

if "GOOGLE_API_KEY" not in os.environ:
    raise ValueError("FATAL: GOOGLE_API_KEY environment variable not set. Please create a .env file and add your key.")

# Create an instance of the Flask class
app = Flask(__name__)
CORS(app)
chat_sessions = {}

# globla varaible to track chat history:
chat_history = []


###################
## API ENDPOINTS ##
###################

# Your existing root route
@app.route('/')
def hello_world():
    """This function will run when someone visits the root URL."""
    return 'Hello, World!'

# Get Frontend Data
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Receives a message from the frontend and returns a placeholder response.
    """
    data = request.get_json()

    # Updated validation to check for the "text" key
    if not data or 'text' not in data:
        return jsonify({"error": "Invalid request: 'text' key is required"}), 400
    
    print(f"Received text: {data.get('text')}")
    
    return jsonify({"response": data.get('text')})



# Chat with gemini
@app.route('/api/gemini', methods=['POST'])
def gemini_chat():
    data = request.json
    prompt = data.get("prompt", "")

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    response = client.models.generate_content(
        model="gemma-3-27b-it", 
        contents= "chat history: " ",".join(chat_history) + "new prompt: " + prompt
    )

    # update chat history
    chat_history.append("user: " + prompt)
    chat_history.append("computer: " + response.text)

    # return text response
    return jsonify({"response": response.text})



# --- Running the Application ---

# This is the standard entry point for a Python script.
if __name__ == '__main__':
    # The app.run() method starts the Flask development server.
    app.run(debug=True, port=5000)