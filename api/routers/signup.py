from fastapi import APIRouter, HTTPException, status
from ..schemas import CreateUser, CreateUserResponse
from ..supabase import supabase
from gotrue.errors import AuthApiError

router = APIRouter(
    tags=["Sign Up"],
    prefix="/signup"
)

@router.post("/", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def sign_up_user(request: CreateUser):
    """Sign up a new user using Supabase Auth"""
    try:
        # Use Supabase authentication to create user
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "username": request.username,
                    "age": request.age
                }
            }
        })

        if auth_response.user:
            return CreateUserResponse(
                uuid=auth_response.user.id,
                username=request.username,
                message="User created successfully. Please check your email for verification."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
            
    except AuthApiError as e:
        # Handle specific Supabase authentication errors
        error_message = str(e).lower()
        
        if "email address" in error_message and "invalid" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address format"
            )
        elif "user already registered" in error_message or "already exists" in error_message:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        elif "password" in error_message and ("short" in error_message or "weak" in error_message):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long"
            )
        elif "too many requests" in error_message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many signup attempts. Please try again later"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signup error: {str(e)}"
            )
            
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during signup: {str(e)}"
        )


