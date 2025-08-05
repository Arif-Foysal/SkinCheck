from fastapi import APIRouter, Depends, HTTPException, status
from api import schemas
from api.supabase_client import supabase
router = APIRouter(
    tags=["Authentication"],
    prefix="/auth"  # Prefix for all routes in this router
)

@router.post("/", status_code=status.HTTP_200_OK)
async def authenticate_user(email: str, password: str):
    user = supabase.auth.sign_in_with_password({ "email": email, "password": password })
    if user:
        return user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

