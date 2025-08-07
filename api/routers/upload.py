import os
import warnings
import hashlib
from typing import List, Optional
from datetime import datetime
from ..schemas import PredictionRequest
from fastapi import APIRouter, HTTPException, UploadFile, status, File, Depends
from fastapi.responses import JSONResponse
from PIL import Image
import io
import uuid
from .auth import get_current_user
from ..schemas import FileUploadResponse, FileValidationError
from ..supabase import supabase
import torch
from torchvision import transforms
from transformers import ViTForImageClassification
import io

router = APIRouter(
    tags=["Upload and Predict"],
    prefix="/predict"
)


# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
    "image/bmp": [".bmp"],
    "image/tiff": [".tiff", ".tif"]
}
ALLOWED_EXTENSIONS = [ext for extensions in ALLOWED_IMAGE_TYPES.values() for ext in extensions]

base_url = os.environ.get("IMAGE_BASE_URL")

# Suppress warnings for deprecated features
warnings.filterwarnings("ignore")

# pretrained model
MODEL_PATH = os.environ.get("MODEL_PATH", "../vit_checkpoint.pth")
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class SkinCancerPredictor:
    def __init__(self, model_path, device='cpu'):
        self.device = device
        self.model = self._load_model(model_path)
        self.transform = self._get_transform()
        self.binary_class_names = {0: "Benign", 1: "Malignant"}
        self.benign_indices = [0, 3, 4, 6]
        self.malignant_indices = [1, 2, 5]

    def _load_model(self, model_path):
        model = ViTForImageClassification.from_pretrained(
            'google/vit-base-patch16-224-in21k',
            num_labels=7,
            ignore_mismatched_sizes=True
        )
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.to(self.device)
        model.eval()
        return model

    def _get_transform(self):
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def predict(self, image: Image.Image):
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = self.model(input_tensor)
            probabilities_7_class = torch.softmax(outputs.logits, dim=1).squeeze(0)
        prob_benign = probabilities_7_class[self.benign_indices].sum().item()
        prob_malignant = probabilities_7_class[self.malignant_indices].sum().item()
        total_prob = prob_benign + prob_malignant
        if total_prob > 0:
            prob_benign /= total_prob
            prob_malignant /= total_prob
        predicted_index = 0 if prob_benign > prob_malignant else 1
        predicted_class = self.binary_class_names[predicted_index]
        confidence = max(prob_benign, prob_malignant)
        return {
            "prediction": predicted_class,
            "confidence": round(confidence, 4),
            "probabilities": {
            "Benign": round(prob_benign, 4),
            "Malignant": round(prob_malignant, 4)
            }
        }

# Load model at startup
predictor = SkinCancerPredictor(model_path=MODEL_PATH, device=DEVICE)



class ImageValidator:
    """Comprehensive image validation class"""
    
    @staticmethod
    def validate_file_size(file_size: int) -> None:
        """Validate file size"""
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
    
    @staticmethod
    def validate_file_type(content_type: str, filename: str) -> None:
        """Validate file type based on MIME type and extension"""
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {list(ALLOWED_IMAGE_TYPES.keys())}"
            )
        
        file_extension = os.path.splitext(filename.lower())[1]
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension. Allowed extensions: {ALLOWED_EXTENSIONS}"
            )
        
        # Cross-check MIME type with extension
        if file_extension not in ALLOWED_IMAGE_TYPES.get(content_type, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File extension doesn't match the file type"
            )
    
    @staticmethod
    async def validate_image_content(file_content: bytes) -> None:
        """Validate actual image content using PIL"""
        try:
            with Image.open(io.BytesIO(file_content)) as img:
                # Verify it's a valid image
                img.verify()
                
                # Reset image for further processing
                img = Image.open(io.BytesIO(file_content))
                
                # Check image dimensions (optional)
                width, height = img.size
                if width < 100 or height < 100:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Image too small. Minimum dimensions: 100x100 pixels"
                    )
                
                if width > 4096 or height > 4096:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Image too large. Maximum dimensions: 4096x4096 pixels"
                    )
                    
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image file: {str(e)}"
            )
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Sanitize and validate filename"""
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename cannot be empty"
            )
        
        # Remove path components for security
        filename = os.path.basename(filename)
        
        # Check for suspicious characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in filename for char in invalid_chars):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename contains invalid characters"
            )
        
        if len(filename) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename too long"
            )
    
        return filename

def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content"""
    return hashlib.sha256(content).hexdigest()

@router.post("/")
async def upload_file(
    image: UploadFile = File(...),  # Required field
    current_user: dict = Depends(get_current_user),
    prediction_request: PredictionRequest = Depends()
):
    """Upload an image file to Supabase storage"""
    # Production-level validation for file upload
    if not image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    if not image.filename or image.filename.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file: filename is empty"
        )
    
    if not image.size or image.size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file: file is empty"
        )
    
    # Validate file size
    ImageValidator.validate_file_size(image.size)
    
    # Validate file type and extension
    ImageValidator.validate_file_type(image.content_type, image.filename)
    
    # Read file content
    file_content = await image.read()

    # Validate image content
    await ImageValidator.validate_image_content(file_content)
    image_rgb = Image.open(io.BytesIO(file_content)).convert('RGB')

    # Predict skin cancer using the loaded model
    prediction_result = predictor.predict(image_rgb)
    # Sanitize and validate filename
    sanitized_filename = ImageValidator.validate_filename(image.filename)
    # Create a unique filename to avoid collisions
    sanitized_filename = f"{uuid.uuid4()}_{sanitized_filename}"
    # Calculate file hash
    file_hash = calculate_file_hash(file_content)

    # Upload to Supabase storage
    bucket_name = os.environ.get("SUPABASE_BUCKET")
    upload_response = supabase.storage.from_(bucket_name).upload(
        f"{sanitized_filename}",
        file_content,
        {"content_type": image.content_type}
    )
    if not upload_response.path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong. Failed to upload file to storage"
        )
    response = supabase.table("uploads").insert({
        "file_name": sanitized_filename,
        "file_hash": file_hash,
        "user_uuid": current_user.get("sub"),  # Assuming user_id is obtained from the current user context
        "localization": prediction_request.localization,
        "url": upload_response.fullPath,
        "prediction_result": prediction_result.get("prediction"),
        "prediction_confidence": prediction_result.get("confidence"),
    }).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file metadata in database"
        )

    if not base_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="IMAGE_BASE_URL environment variable is not set"
        )
    # Return the file upload response
    live_url = f"{base_url}/{response.data[0]['url']}"

    return JSONResponse(content=prediction_result,status_code=status.HTTP_201_CREATED, headers={
        "X-File-Name": sanitized_filename,
        "X-File-Hash": file_hash,
        "X-File-URL": live_url
    })

@router.get("/history", status_code=status.HTTP_200_OK)
async def get_upload_history(current_user: dict = Depends(get_current_user)):
    """Get upload history for the current user"""
    user_uuid = current_user.get("sub")
    if not user_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    
    try:
        response = supabase.table("uploads").select("*").eq("user_uuid", user_uuid).execute()
        if not response.data:
            return {"message": "No uploads found for this user"}
        user_uploads = response.data
        for upload in user_uploads:
            upload['url'] = f"{base_url}/{upload['url']}" if base_url else upload['url']
        return {"uploads": user_uploads}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving upload history: {str(e)}"
        )