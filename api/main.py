from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .routers import auth, upload, signup, supabase_test, user
from .middlewares.auth import auth_middleware
from .middlewares.logger import log_requests

app = FastAPI(
    title="SkinCheck API",
    description="Production-level API for skin analysis",
    version="1.0.0"
)

# Global exception handlers for production
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages"""
    errors = exc.errors()
    
    # Check for common file upload errors
    for error in errors:
        if "image" in error.get("loc", []):
            if error.get("type") == "value_error":
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Invalid file upload",
                        "message": "Please provide a valid image file",
                        "code": "INVALID_FILE"
                    }
                )
            elif error.get("type") == "missing":
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Missing required file",
                        "message": "Image file is required",
                        "code": "MISSING_FILE"
                    }
                )

    # Generic validation error
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation error",
            "message": "Invalid request data provided",
            "code": "VALIDATION_ERROR"
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Invalid data",
            "message": "The provided data is invalid",
            "code": "INVALID_DATA"
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "code": "INTERNAL_ERROR"
        }
    )
# Middleware (order matters - added from bottom to top)
app.middleware("http")(log_requests)
app.middleware("http")(auth_middleware)

# Include routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(signup.router)
app.include_router(supabase_test.router)
app.include_router(user.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SkinCheck API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": "2025-08-06T00:00:00Z",
        "version": "1.0.0"
    }
