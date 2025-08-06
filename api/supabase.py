import os
import uuid
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
from fastapi import HTTPException, Header, status, Depends
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")

supabase: Client = create_client(url, key)


def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user = supabase.auth.get_user(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

