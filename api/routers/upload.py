from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

router = APIRouter(
    tags=["Upload"],
    prefix="/upload"  # Prefix for all routes in this router
)

@router.post("/")
async def upload_file():
    return {"message": "File uploaded successfully"}

