from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    name: str
    age: int
    income: Optional[float] = None
    household_size: Optional[int] = None
    location: Optional[str] = None