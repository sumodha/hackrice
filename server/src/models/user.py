from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    name: str
    age: int
    income: Optional[int] = None
    household_size: Optional[int] = None
    sex: Optional[bool] = None
    citizenship: list[bool]
    address: Optional[bool] = None
    monthly_income: Optional[int] = None
    employment: Optional[bool] = None
    disability_status: Optional[bool] = None
    veteran: Optional[bool] = None
    criminal_record: Optional[bool] = None
    child: Optional[bool] = None