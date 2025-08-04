from fastapi import APIRouter, Depends, HTTPException, status
from api import schemas
router = APIRouter(
    tags=["Authentication"],
    prefix="/auth"  # Prefix for all routes in this router
)

@router.post("/", response_model=schemas.AuthResponse)
async def authenticate_user(username: str, password: str):
    if username == "admin" and password == "password":
        return {"access_token": "fake_access_token", "token_type": "bearer"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

