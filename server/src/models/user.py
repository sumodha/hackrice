from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    age: Optional[int] = None
    citizen_or_lawful_resident: Optional[bool] = None
    has_permanent_address: Optional[bool] = None
    lives_with_people: Optional[bool] = None
    monthly_income: Optional[int] = None
    employed: Optional[bool] = None
    disabled: Optional[bool] = None
    is_veteran: Optional[bool] = None
    has_criminal_record: Optional[bool] = None
    has_children: Optional[bool] = None
    is_refugee: Optional[bool] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_field(self, field_name: str, value) -> None:
        """
        Set a field value by name.

        Args:
            field_name (str): The name of the field to set.
            value: The value to assign to the field.
        """
        if field_name in self.__dict__:
            setattr(self, field_name, value)