from pydantic import BaseModel
from datetime import datetime
from app.models.file import FileVisibility
from app.schemas.user import User

class FileBase(BaseModel):
    filename: str
    visibility: FileVisibility

class FileCreate(FileBase):
    pass

class FileUpdate(FileBase):
    pass

class FileInDBBase(FileBase):
    id: int
    owner_id: int
    department: str
    size: int
    downloads: int
    created_at: datetime
    owner: User

    class Config:
        orm_mode = True

class File(FileInDBBase):
    pass
