from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from src.core.models import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True