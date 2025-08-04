from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(
    tags=["Prediction"],
    prefix="/predict"  # Prefix for all routes in this router
)

@router.post("/")
async def predict():
    return {"message": "Prediction successful"}

