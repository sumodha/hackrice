import os
from google import genai

# --- 1. API Key Configuration ---
# Load the API key from an environment variable for security.
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable not set")


# --- 2. Chatbot Class ---
class Chatbot:
    """
    A class to encapsulate the Gemini model and manage chat sessions.
    """
    def __init__(self, model_name='gemini-1.5-flash'):
        """Initializes the chatbot model and session storage."""
        # Initialize the generative model with a system instruction
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction='You are a helpful and friendly chatbot. Provide clear and concise answers.'
        )
        # In-memory storage for active chat sessions {session_id: chat_object}
        # Note: This is for demonstration. For production, you'd use a database
        # or a more persistent cache like Redis.
        self.sessions = {}

    def start_new_session(self):
        """Starts a new chat session with the model."""
        # The history is managed by the chat object itself after starting.
        return self.model.start_chat(history=[])

    def chat(self, session_id: str, prompt: str) -> str:
        """
        Handles an incoming message for a given session, maintaining context.

        Args:
            session_id: A unique identifier for the conversation.
            prompt: The user's message.

        Returns:
            The model's text response.
        """
        # Get the chat session for the given ID, or create a new one if it doesn't exist.
        if session_id not in self.sessions:
            print(f"Starting new session for ID: {session_id}")
            self.sessions[session_id] = self.start_new_session()
        
        # Get the specific chat session
        chat_session = self.sessions[session_id]
        
        # Send the user's prompt to the model
        response = chat_session.send_message(prompt)
        
        return response.text


# # chatbot.py
# import getpass
# import os
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import HumanMessage
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.graph import START, MessagesState, StateGraph

# from dotenv import load_dotenv

# # APIs
# load_dotenv()
# os.environ["LANGSMITH_TRACING"] = "true"
# os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY")

# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# class ChatBot:
#     def __init__(self, model_name="gemma-3-27b-it"):
#         # Initialize Gemini model (requires GOOGLE_API_KEY in environment)
#         self.model = ChatGoogleGenerativeAI(model=model_name)

#         # Build workflow graph
#         workflow = StateGraph(state_schema=MessagesState)

#         def call_model(state: MessagesState):
#             response = self.model.invoke(state["messages"])
#             return {"messages": response}

#         workflow.add_node("model", call_model)
#         workflow.add_edge(START, "model")

#         # In-memory conversation persistence
#         memory = MemorySaver()
#         self.app = workflow.compile(checkpointer=memory)

#     def chat(self, message: str, thread_id: str = "default") -> str:
#         """Send a message to the chatbot and return its response."""
#         input_messages = [HumanMessage(message)]
#         config = {"configurable": {"thread_id": thread_id}}

#         output = self.app.invoke({"messages": input_messages}, config)
#         return output["messages"][-1].content
