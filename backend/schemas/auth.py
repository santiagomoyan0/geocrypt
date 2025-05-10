from pydantic import BaseModel
from datetime import datetime
from models import UserBase

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True 