from fastapi import APIRouter, Depends, HTTPException,Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.responses import Response
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..schemas import SignUpRequest, AuthResponse
from ..supabase import supabase
from gotrue.errors import AuthApiError
from os import getenv


supabase_jwt_secret: str = getenv("SUPABASE_JWT_SECRET")
security = HTTPBearer()

router = APIRouter(
    tags=["Authentication"],
    prefix="/auth"  # Prefix for all routes in this router
)


# async def auth_middleware(request: Request, call_next):
#     token = request.cookies.get("access_token")
#     if token and token.startswith("Bearer "):
#         token = token.split(" ")[1]  # Extract the actual token
#         request.headers.__dict__["_list"].append(
#             (b"authorization", f"Bearer {token}".encode())
#         )
#     response = await call_next(request)
#     return response


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        
        # Use Supabase's built-in user verification
        user_response = supabase.auth.get_user(token)
        
        if user_response and user_response.user:
            # Return user data in a format similar to JWT payload
            return {
                "sub": user_response.user.id,
                "email": user_response.user.email,
                "aud": "authenticated",
                "role": user_response.user.role if hasattr(user_response.user, 'role') else "authenticated",
                "user_metadata": user_response.user.user_metadata,
                "app_metadata": user_response.user.app_metadata
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid authentication credentials"
            )
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Could not validate credentials"
        )

@router.post("/", status_code=status.HTTP_200_OK)
async def authenticate_user(response: Response, email: str, password: str):
    """Authenticate user with Supabase and return session info"""
    try:
        # Attempt to sign in with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": email, 
            "password": password
        })
        
        if auth_response.user and auth_response.session:
            access_token = auth_response.session.access_token
            response.set_cookie(
                key="access_token",
                value=f"Bearer {access_token}",
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax"
            )
            return {
                "user_id": auth_response.user.id,
                "email": auth_response.user.email,
                "access_token": access_token,
                "token_type": "bearer",
                "message": "Authentication successful"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed - invalid credentials"
            )
            
    except AuthApiError as e:
        # Handle specific Supabase authentication errors
        error_message = str(e).lower()
        
        if "invalid login credentials" in error_message or "invalid credentials" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        elif "email not confirmed" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please verify your email address before signing in"
            )
        elif "too many requests" in error_message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authentication error: {str(e)}"
            )
            
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during authentication: {str(e)}"
        )
    

@router.get("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )
    return {
        "status": "success",
        "message": "Logged out successfully"
    }

@router.get("/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile (protected endpoint)
    
    This endpoint requires authentication. Use the 'Authorize' button in FastAPI docs.
    """
    return {
        "user_id": current_user.get("sub"),
        "email": current_user.get("email"),
        "role": current_user.get("role", "authenticated"),
        "user_metadata": current_user.get("user_metadata", {}),
        "app_metadata": current_user.get("app_metadata", {})
    }