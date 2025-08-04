from fastapi import APIRouter, Depends, HTTPException, status
from api import schemas
router = APIRouter(
    tags=["Sign Up"],
    prefix="/signup"  # Prefix for all routes in this router
)

@router.post("/", response_model=schemas.CreateUserResponse,status_code=status.HTTP_201_CREATED)
async def sign_up_user(request: schemas.CreateUser):
    # Here you would typically hash the password and save the user to the database if there is no existing user with the same username or email.
    return {"uuid": 1, "username": request.username}
    

