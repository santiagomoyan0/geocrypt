from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class UserBase(SQLModel):
    username: str
    email: str

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FileModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    s3_key: str
    geohash: str
    user_id: int = Field(foreign_key="user.id")
    size: int
    content_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow) 