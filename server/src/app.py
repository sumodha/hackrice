import os
from google import genai


from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# APIs
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key = GEMINI_API_KEY)

# Create an instance of the Flask class
app = Flask(__name__)
CORS(app)

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
        contents=prompt
    )

    # return text response
    return jsonify({"response": response.text})



# --- Running the Application ---

# This is the standard entry point for a Python script.
if __name__ == '__main__':
    # The app.run() method starts the Flask development server.
    app.run(debug=True, port=5000)