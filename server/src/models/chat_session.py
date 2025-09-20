from pydantic import BaseModel
from typing import List, Optional
from .user import User

class ChatMessage(BaseModel):
    sender: str  # 'user' or 'bot'
    message: str

class ChatSession(BaseModel):
    session_id: str
    user: User
    messages: List[ChatMessage] = []
    current_stage: str  # 'intake', 'recommendation', 'eligibility'