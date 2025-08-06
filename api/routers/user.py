from fastapi import APIRouter, Depends, HTTPException, status
from ..supabase import supabase
from .auth import get_current_user

router = APIRouter(
    tags=["User Management"],
    prefix="/user"  # Prefix for all routes in this router
)

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user's information"""
    user_id = current_user.get('sub')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")

    response = current_user

    return response.get('user_metadata', {})