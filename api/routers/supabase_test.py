from api.supabase_client import supabase
from fastapi import HTTPException, status, APIRouter
from typing import List
from api import schemas


router = APIRouter(
    tags=["CRUD TEST"],
    prefix="/test"  # Prefix for all routes in this router
)

@router.get("/" , status_code=status.HTTP_200_OK)
async def get_items():
    """Get all items"""
    try:
        response = supabase.table("items").select("*").execute()
        return response.data or []
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
