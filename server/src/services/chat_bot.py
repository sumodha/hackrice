# chatbot.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

from dotenv import load_dotenv

# APIs
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class ChatBot:
    def __init__(self, model_name="gemma-3-27b-it"):
        # Initialize Gemini model (requires GOOGLE_API_KEY in environment)
        self.model = ChatGoogleGenerativeAI(model=model_name)

        # Build workflow graph
        workflow = StateGraph(state_schema=MessagesState)

        def call_model(state: MessagesState):
            response = self.model.invoke(state["messages"])
            return {"messages": response}

        workflow.add_node("model", call_model)
        workflow.add_edge(START, "model")

        # In-memory conversation persistence
        memory = MemorySaver()
        self.app = workflow.compile(checkpointer=memory)

    def chat(self, message: str, thread_id: str = "default") -> str:
        """Send a message to the chatbot and return its response."""
        input_messages = [HumanMessage(message)]
        config = {"configurable": {"thread_id": thread_id}}

        output = self.app.invoke({"messages": input_messages}, config)
        return output["messages"][-1].content
