import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.concurrency import run_in_threadpool
from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_KEY
from src.utils.security import sanitize_error_message

logger = logging.getLogger(__name__)

security = HTTPBearer()

def get_supabase_client(user_token: Optional[str] = None) -> Client:
    """
    Returns an initialized Supabase Python client.
    If user_token is provided, authenticates PostgREST requests with the user's JWT
    so PostgreSQL Row Level Security (RLS) policies see auth.uid().
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase credentials are not configured on backend."
        )
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if user_token:
        client.postgrest.auth(user_token)
    return client

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict[str, Any]:
    """
    Validates Supabase JWT token passed in Authorization header.
    Returns user dictionary containing id, email, metadata, and token.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token"
        )
    
    try:
        supabase = await run_in_threadpool(get_supabase_client)
        # Verify JWT token with Supabase auth
        user_response = await run_in_threadpool(supabase.auth.get_user, token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token."
            )
        
        user = user_response.user
        return {
            "id": user.id,
            "email": user.email,
            "user_metadata": user.user_metadata or {},
            "token": token
        }
    except HTTPException:
        raise
    except Exception as e:
        sanitized_err = sanitize_error_message(str(e))
        logger.error(f"Authentication verification failed: {sanitized_err}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token."
        )
