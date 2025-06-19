from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    provider: str
    redirect_uri: Optional[str] = None

class LoginResponse(BaseModel):
    auth_url: str
    state: str

class CallbackRequest(BaseModel):
    code: str
    state: str

class UserProfile(BaseModel):
    id: int
    email: Optional[str]
    username: str
    avatar_url: Optional[str]
    is_active: bool
    created_at: Optional[datetime]

class AuthResponse(BaseModel):
    success: bool
    user: Optional[UserProfile] = None
    message: str