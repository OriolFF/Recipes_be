from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserDisplay(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True # For Pydantic V1, or from_attributes = True for V2

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None
