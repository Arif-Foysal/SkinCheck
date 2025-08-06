from api.supabase import supabase
from fastapi import Depends, HTTPException, status, APIRouter
from typing import List
from api import schemas
from .auth import get_current_user

router = APIRouter(
    tags=["CRUD TEST"],
    prefix="/test"  # Prefix for all routes in this router
)

@router.get("/" , status_code=status.HTTP_200_OK)
async def get_items(current_user: dict = Depends(get_current_user)):
    """Get all items"""
    try:
        response = supabase.table("items").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
@router.get("/{item_id}",  status_code=status.HTTP_200_OK)
async def get_item(item_id: int):
    """Get item by ID"""
    response = supabase.table("items").select("*").eq("id", item_id).execute()
    if response.data:
        return response.data[0]
    raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

@router.post("/",status_code=status.HTTP_201_CREATED)    
async def create_item(content:str):
    response = supabase.table("items").insert({"content": content}).execute()
    if response.data:
        return response.data[0]
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to create item"
    )
