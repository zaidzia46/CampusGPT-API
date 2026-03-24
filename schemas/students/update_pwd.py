from pydantic import BaseModel

class UpdatePassword(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str