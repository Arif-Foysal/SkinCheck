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
    try:
        user_id = current_user.get('sub')
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated")
        
        response = supabase.auth.api.get_user(user_id)
        if response.user:
            return response.user
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user information: {str(e)}"
        )