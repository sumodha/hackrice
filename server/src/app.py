import os
import json
import pandas as pd


from google import genai
from google.genai import types

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from services import stochastic_query
from services import rank_programs_bot
from models import user

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

with open("data/social_links.json", "r") as f:
    data_link = json.load(f)

chat_a_history = []
chat_a_sessions = {}
chat_a_questions_asked = 0
chat_a_system = f"""System prompt: You are a social welfare expert who's task is to help users figure out their needs and connect them to as many social welfare programs through natural conversations. 
Keep answers short and concise. Only ask one question per response. These questions should be broad."""
chat_a_reference = """Only reference and reconmend wellfare programs from this JSON: """ + json.dumps(data)
chat_a_switch = """Based on your answers, we found the following programs to match your need the most: """

stage_var = "a" ## must be a or b

## Global variables for Stage B
stage_b_history = ""
stage_b_potentials = []
query_user = stochastic_query.query_user()
stage_b_questions_asked = 0
programs_df = pd.read_csv("data/All_Programs_Data.csv")
my_user = user.User()
emergency = []



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


# Stage a logic
@app.route('/api/chat/a', methods=['POST'])
def stage_a_chat():
    global chat_a_history, chat_a_questions_asked, stage_var, stage_b_potentials, stage_b_history, chat_a_switch, emergency

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
            Example Output: ['Supplemental Nutrition Assistance Program (SNAP)', 'Medicaid', 'Supportive Housing for the Elderly (Section 202)', ...] \n""" + f"Chat history: {",".join(chat_a_history)} \n" + f"JSON of sources: {chat_a_reference}" 
        )

        # 2 convert output into a list
        output = response.text[1:-1]
        output = output.split(", ") ## makes a list 

        # 3. change stage flag
        stage_var = 'b'
        stage_b_history = ",".join(chat_a_history)
        stage_b_potentials = output

        # 4. Parse response for frontend
        pot_progs = []
        for prog in output:
            pot_progs.append({"name" : prog.strip("'"),
                             "description" : data.get(prog.strip("'"), ""),
                             "link" : data_link.get(prog.strip("'"),"")})
            
        chat_a_switch += "\n\n\n Click buttons to view programs in more detail and check elgibility!"
        print(pot_progs)
        emergency = pot_progs
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
    return jsonify({"text": response.text.strip(), "programs" : []})


# Stage B logic
@app.route('/api/chat/b', methods=['POST'])
def stage_b_chat():
    global query_user, stage_b_questions_asked, programs_df, stage_b_potentials, my_user, emergency

    input_data = request.json
    answer = input_data.get("text", "")

    # add answer to query user's string context
    query_user.update_responses(f"User: {answer}; ")


    if stage_b_questions_asked > 5:
        ## update my user
        user_fields = ["age", "citizen_or_lawful_resident", "has_permanent_address", "lives_with_people", "monthly_income", "employed", "disabled", "is_veteran", "has_criminal_record", "has_children", "is_refugee"]
        all_user_responses = query_user.get_all_responses()
        user_fill_response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents= f"chat history: {all_user_responses}" + "\n" + f"Fields: {", ".join(user_fields)}" + "\n" + f'Task: create a JSON where every field is a string key that matches to a string value extracted from the chat history. monthly income should be an int (represented with a string), and every other field should be a boolean (represented with a string). Only return this output json and nothing else (example, no ``` or ```json). Do not include an extra headers or symbols that are not the JSON itself. Example output: {{"employed" : "False", "monthly_income" : "100"}}'
        )

        print(user_fill_response.text)
        my_user.set_fields(json.loads(user_fill_response.text))

        rank_bot = rank_programs_bot.RankProgramsBot(programs_df, stage_b_potentials, my_user)
        ranked_programs = rank_bot.rank_programs()

        # 4. Parse response for frontend
        f_programs = []
        for prog in ranked_programs:
            f_programs.append({"name" : prog.strip("'"),
                             "description" : data.get(prog.strip("'"), ""),
                             "link" : data_link.get(prog.strip("'"), "")})
            
        my_user.print_all_fields()
        print(f_programs)
        if len(f_programs) == 0:
            f_programs = emergency[:len(emergency)//2]
            print(stage_b_potentials)
        return jsonify({"text": "Programs are listed in order of elgibility:", "programs": f_programs})

    # ask next question
    question = query_user.next_question()
    print("question", question)

    # add question to string context
    query_user.update_responses(f"model: {question}; ")

    stage_b_questions_asked += 1

    return jsonify({"text": question, "programs": []})

    

# send stage route
@app.route("/api/stage", methods=["GET"])
def get_stage():
    return jsonify({"stage": stage_var})



# --- Running the Application ---

# This is the standard entry point for a Python script.
if __name__ == '__main__':
    # The app.run() method starts the Flask development server.
    app.run(debug=True, port=5000)