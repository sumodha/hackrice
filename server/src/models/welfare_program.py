from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class WelfareProgram(BaseModel):
    name: str
    description: str
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    sex: Optional[bool] = None
    citizenship: list[bool]
    address: Optional[bool] = None
    household_size: Optional[bool] = None
    max_monthly_income: Optional[int] = None
    employment_required: Optional[bool] = None
    disability_status: Optional[bool] = None
    veteran: Optional[bool] = None
    criminal_record: Optional[bool] = None
    child: Optional[bool] = None