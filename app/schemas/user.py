from pydantic import BaseModel
from app.models.user import UserRole

class UserBase(BaseModel):
    username: str
    department: str

class UserCreate(UserBase):
    password: str
    role: UserRole

class UserUpdate(UserBase):
    pass

class UserInDBBase(UserBase):
    id: int
    role: UserRole

    class Config:
        orm_mode = True

class User(UserInDBBase):
    pass
