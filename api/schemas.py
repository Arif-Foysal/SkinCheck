from pydantic import BaseModel, EmailStr

class CreateUser(BaseModel):
    username: str
    password: str
    email: EmailStr
    age: int

class CreateUserResponse(BaseModel):
    uuid: int
    username: str


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str




