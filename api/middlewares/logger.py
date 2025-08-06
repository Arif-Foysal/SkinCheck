from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from ..routers.auth import get_current_user
from fastapi.security import HTTPAuthorizationCredentials

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logger = logging.getLogger("api-logger")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

async def log_requests(request: Request, call_next):
    ip = request.client.host
    auth_header = request.headers.get("authorization", "")
    email = "anonymous"
    user_id = None

    if auth_header.startswith("Bearer "):
        try:
            # Create credentials object for get_current_user
            from fastapi.security import HTTPAuthorizationCredentials
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=auth_header.replace("Bearer ", "")
            )
            
            # Use the auth router's get_current_user function
            user_data = get_current_user(credentials)
            user_id = user_data.get("sub")
            email = user_data.get("email", "no_email")
            
        except Exception as e:
            # If authentication fails, keep defaults
            email = "auth_failed"
            user_id = None
    
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")

    # Log complete request and response to Supabase
    try:
        supabase.table("logs").insert({
            "method": request.method,
            "path": request.url.path,
            "user_id": user_id,
            "ip": ip,
            "status_code": response.status_code,
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log to Supabase: {e}")

    return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        return await log_requests(request, call_next)
