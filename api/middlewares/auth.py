from fastapi import APIRouter, Depends, HTTPException,Request, status
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..schemas import SignUpRequest, AuthResponse
from ..supabase import supabase
from gotrue.errors import AuthApiError
from os import getenv
# to be used later for JWT secret

supabase_jwt_secret: str = getenv("SUPABASE_JWT_SECRET")
security = HTTPBearer()

router = APIRouter(
    tags=["Authentication"],
    prefix="/auth"  # Prefix for all routes in this router
    )


async def auth_middleware(request: Request, call_next):
    print("Auth middleware triggered")
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]  # Extract the actual token
        request.headers.__dict__["_list"].append(
            (b"authorization", f"Bearer {token}".encode())
        )
    response = await call_next(request)
    return response