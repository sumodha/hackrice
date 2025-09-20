from pydantic import BaseModel
from typing import List, Dict, Any

class WelfareProgram(BaseModel):
    id: int
    name: str
    description: str
    eligibility_criteria: Dict[str, Any]
    benefits: List[str]