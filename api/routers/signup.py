import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, status
from api import schemas
from api.supabase_client import supabase
from passlib.context import CryptContext

router = APIRouter(
    tags=["Sign Up"],
    prefix="/signup"
)

# Use bcrypt for password hashing (more secure than SHA-256)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def sign_up_user(request: schemas.CreateUser):
    """Sign up a new user"""
    try:
        # Hash the password before storing
        # Create user in database using Supabase function
       #use supabase auth to create user
        user_data = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "data": {
                "username": request.username,
                "age": request.age
            }
        })

        # Return response with user ID and username
        return user_data
        
    except HTTPException:
        # Re-raise HTTP exceptions (like username/email already exists)
        raise
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


