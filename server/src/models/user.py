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

   # Corrected __init__
    def __init__(self, **kwargs):
        # This line is crucial! It runs Pydantic's setup.
        super().__init__(**kwargs) 
        print("User object initialized!")

    def set_fields(self, json_data: dict):
        for field_name, value in json_data.items():
            if field_name in self.__fields__:
                field_type = type(self.__fields__[field_name])
                
                # Handle boolean fields
                if field_type == bool and isinstance(value, str):
                    value_lower = value.lower()
                    if value_lower in {"true", "1", "yes"}:
                        value = True
                    elif value_lower in {"false", "0", "no"}:
                        value = False
                    else:
                        # Invalid boolean string, skip or set None
                        value = None

                # Optionally handle int fields coming as strings
                if field_type == int and isinstance(value, str):
                    try:
                        value = int(value)
                    except ValueError:
                        value = None  # invalid int, skip or set None

                setattr(self, field_name, value)




    def set_field(self, field_name: str, value) -> None:
        """
        Set a field value by name.

        Args:
            field_name (str): The name of the field to set.
            value: The value to assign to the field.
        """
        if field_name in self.__dict__:
            setattr(self, field_name, value)


    def print_all_fields(self):
        """
        Print every field and its current value in the User class.
        """
        print("User Fields:")
        print("-" * 40)
        for field_name, field_info in self.__fields__.items():
            value = getattr(self, field_name, None)
            field_type = field_info.annotation if hasattr(field_info, 'annotation') else field_info.type_
            print(f"{field_name}: {value} (Type: {field_type})")
        print("-" * 40)