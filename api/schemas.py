from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class CreateUser(BaseModel):
    username: str
    password: str
    email: EmailStr
    age: int

class CreateUserResponse(BaseModel):
    uuid: str  # Supabase UUIDs are strings
    username: str
    message: str

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_size: int
    file_type: str
    upload_url: Optional[str] = None
    message: str
    uploaded_at: datetime

class FileValidationError(BaseModel):
    error: str
    details: str
    allowed_types: list[str]
    max_size_mb: int

class PredictionRequest(BaseModel):
    localization: str

