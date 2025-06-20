from pydantic import BaseModel, ConfigDict
from typing import Optional
from utils.datetime import Datetime2Timestamp

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
    created_at: Optional[Datetime2Timestamp]

class AuthResponse(BaseModel):
    success: bool
    user: Optional[UserProfile] = None
    message: str