import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from src.api.auth import get_supabase_client
from src.utils.security import encryption_service
from src.services.github_service import github_service

logger = logging.getLogger(__name__)

class GitHubCredentialsService:
    """
    Database service managing github_credentials table in Supabase PostgreSQL.
    Forwarding user_token ensures PostgREST sends Authorization: Bearer <user_token>
    so PostgreSQL Row Level Security (RLS) policies accurately verify auth.uid() = user_id.
    """

    TABLE_NAME = "github_credentials"

    def _handle_db_error(self, e: Exception, operation: str) -> None:
        """
        Helper method to translate Supabase / PostgREST exceptions into HTTP Exceptions.
        """
        err_msg = str(e)
        logger.error(f"Database failure during {operation}: {err_msg}")
        
        if "PGRST205" in err_msg or "Could not find the table" in err_msg or "relation" in err_msg and "does not exist" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database Error: Table 'public.github_credentials' does not exist in Supabase. Please execute the SQL migration in Supabase SQL Editor."
            )
        elif "PGRST301" in err_msg or "42501" in err_msg or "permission denied" in err_msg.lower() or "row-level security policy" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Database Error: Permission denied by Supabase Row Level Security (RLS) policies. Please verify RLS policies in Supabase SQL Editor."
            )
        elif "23505" in err_msg or "duplicate key" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Database Error: A GitHub account is already connected for this user."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database query error during {operation}: {err_msg}"
            )

    def get_credential(self, user_id: str, user_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches GitHub credential metadata for the given user_id.
        Does NOT return the decrypted or encrypted token.
        """
        try:
            supabase = get_supabase_client(user_token)
            res = supabase.table(self.TABLE_NAME).select(
                "id, user_id, github_username, github_user_id, github_avatar_url, created_at, updated_at"
            ).eq("user_id", user_id).execute()

            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except HTTPException:
            raise
        except Exception as e:
            self._handle_db_error(e, "fetch credential")
            return None

    async def connect_credential(self, user_id: str, token: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        1. Validates PAT with GitHub API
        2. Encrypts PAT using Fernet
        3. Upserts credential record into public.github_credentials in Supabase PostgreSQL
        4. Returns metadata
        """
        # Validate PAT against GitHub API
        github_info = await github_service.validate_token_and_get_user(token)

        # Encrypt token securely
        try:
            encrypted_pat = encryption_service.encrypt(token.strip())
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Encryption failure while securing Personal Access Token."
            )

        payload = {
            "user_id": user_id,
            "github_username": github_info["username"],
            "github_user_id": github_info["github_user_id"],
            "github_avatar_url": github_info["avatar_url"],
            "encrypted_pat": encrypted_pat
        }

        try:
            supabase = get_supabase_client(user_token)
            
            # Atomic upsert on conflict user_id
            res = supabase.table(self.TABLE_NAME).upsert(payload, on_conflict="user_id").execute()

            if not res.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save GitHub credential to database."
                )

            return {
                "message": "Connected Successfully",
                "connected": True,
                "username": github_info["username"],
                "name": github_info["name"],
                "avatar_url": github_info["avatar_url"]
            }

        except HTTPException:
            raise
        except Exception as e:
            self._handle_db_error(e, "connect credential")
            return {}

    def delete_credential(self, user_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Deletes GitHub credential for the specified user_id.
        """
        try:
            supabase = get_supabase_client(user_token)
            supabase.table(self.TABLE_NAME).delete().eq("user_id", user_id).execute()
            return {
                "message": "GitHub account disconnected successfully.",
                "connected": False
            }
        except HTTPException:
            raise
        except Exception as e:
            self._handle_db_error(e, "disconnect credential")
            return {}

    def get_decrypted_pat(self, user_id: str, user_token: Optional[str] = None) -> str:
        """
        Internal service method: Retrieves and decrypts PAT for executing GitHub operations.
        NEVER expose via API routes.
        """
        try:
            supabase = get_supabase_client(user_token)
            res = supabase.table(self.TABLE_NAME).select("encrypted_pat").eq("user_id", user_id).execute()
            if not res.data or len(res.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No connected GitHub account found for user."
                )
            encrypted_pat = res.data[0]["encrypted_pat"]
            return encryption_service.decrypt(encrypted_pat)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error decrypting PAT for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt GitHub access token."
            )

github_credentials_service = GitHubCredentialsService()
