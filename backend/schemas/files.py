from pydantic import BaseModel
from datetime import datetime

class FileBase(BaseModel):
    filename: str
    geohash: str

class FileCreate(FileBase):
    pass

class FileResponse(FileBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True 