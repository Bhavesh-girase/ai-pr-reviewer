import logging
import httpx
from typing import Dict, Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class GitHubService:
    """
    Service for interacting with GitHub REST API endpoints.
    """
    
    GITHUB_API_BASE = "https://api.github.com"
    
    async def validate_token_and_get_user(self, token: str) -> Dict[str, Any]:
        """
        Validates GitHub Personal Access Token against GitHub API (GET /user).
        Returns profile info: username, user_id, avatar_url, display_name.
        """
        if not token or not token.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub Personal Access Token is required."
            )
        
        headers = {
            "Authorization": f"Bearer {token.strip()}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-PR-Reviewer-App"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.GITHUB_API_BASE}/user", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "username": data.get("login"),
                        "github_user_id": data.get("id"),
                        "avatar_url": data.get("avatar_url"),
                        "name": data.get("name") or data.get("login")
                    }
                elif response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired GitHub Personal Access Token."
                    )
                elif response.status_code == 403:
                    rate_limit_remaining = response.headers.get("x-ratelimit-remaining")
                    if rate_limit_remaining == "0":
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="GitHub API rate limit exceeded. Please try again later."
                        )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="GitHub access forbidden. Ensure the Personal Access Token has required permissions."
                    )
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"GitHub API error: {response.text}"
                    )
                    
        except httpx.ConnectError:
            logger.error("Failed to connect to GitHub API.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub service is currently unreachable. Please check your network connection."
            )
        except httpx.TimeoutException:
            logger.error("GitHub API request timed out.")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="GitHub API request timed out."
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected GitHub API error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to communicate with GitHub API: {str(e)}"
            )

github_service = GitHubService()
