import os
import json
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


# globla varaible to track STAGE A chats
with open("data/social_welfare_programs.json", "r") as f:
    data = json.load(f)

chat_a_history = []
chat_a_sessions = {}
chat_a_questions_asked = 0
chat_a_system = f"""System prompt: You are a social welfare expert who's task is to help users figure out their needs and connect them to social welfare programs through natural conversations. 
Keep answers short and concise. Only ask one question per response."""
chat_a_reference = """Only reference and reconmend wellfare programs from this JSON: """ + json.dumps(data)
chat_a_switch = """Based on your answers, we found the following programs to match your need the most: """

stage_var = "a" ## must be a or b

## Global variables for Stage B
stage_b_history = ""
stage_b_potentials = []


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
    input_data = request.get_json()

    # Updated validation to check for the "text" key
    if not input_data or 'text' not in input_data:
        return jsonify({"error": "Invalid request: 'text' key is required"}), 400
    
    print(f"Received text: {input_data.get('text')}")
    
    return jsonify({"response": input_data.get('text')})



# Chat with gemini
@app.route('/api/chat/a', methods=['POST'])
def stage_a_chat():
    global chat_a_history, chat_a_questions_asked, stage_var, stage_b_potentials, stage_b_history, chat_a_switch

    input_data = request.json
    prompt = input_data.get("text", "")

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    print(chat_a_questions_asked)
    if chat_a_questions_asked > 5:
        # 1. prompt chat to get list of programs that would match user needs
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite", 
            contents = """System prompt: You are a social welfare expert who's task is to output a list of social welfare programs that could aid a potential user.
            You are given 1. the chat history of a users personal situation and 2. a JSON of all possible social welfare programs.
            Output: Generate only a comma separated python list of all social welfare programs that would assist the user based on the chat history and nothing else.
            Example Output: [SNAPS, Medicare, TANF, ...] \n""" + f"Chat history: {",".join(chat_a_history)} \n" + f"JSON of sources: {chat_a_reference}" 
        )

        # 2 convert output into a list
        output = response.text[1:-1]
        output = output.split(", ")

        # 3. change stage flag
        stage_var = 'b'
        stage_b_history = ",".join(chat_a_history)
        stage_b_potentials = output

        # 4. Parse response for frontend
        pot_progs = []
        for prog in output:
            pot_progs.append({"name" : prog,
                             "description" : data.get(prog, "")})
            
        chat_a_switch += response.text
        chat_a_switch += "\n\n Use the buttons below to A. Check elgibility for each program or B. View programs in more detail"

        return jsonify({"text": chat_a_switch, "programs" : pot_progs})
    

    response = client.models.generate_content(
        model="gemma-3-27b-it", 
        contents= "chat history: " + ",".join(chat_a_history) + "\n" + "new prompt: " + prompt + chat_a_system
    )

    # update chat history
    chat_a_history.append("user: " + prompt)
    chat_a_history.append("model: " + response.text)
    chat_a_questions_asked += 1

    # return text response
    return jsonify({"text": response.text, "programs" : []})

# send stage route
@app.route("/api/stage", methods=["GET"])
def get_stage():
    return jsonify({"stage": stage_var})



# --- Running the Application ---

# This is the standard entry point for a Python script.
if __name__ == '__main__':
    # The app.run() method starts the Flask development server.
    app.run(debug=True, port=5000)