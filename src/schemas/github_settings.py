from typing import Optional
from pydantic import BaseModel, Field

class GitHubTokenRequest(BaseModel):
    """
    Request model for testing or connecting a GitHub PAT.
    """
    token: str = Field(..., description="GitHub Personal Access Token (classic or fine-grained)", min_length=1)

class GitHubStatusResponse(BaseModel):
    """
    Response model for GET /settings/github endpoint.
    """
    connected: bool
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    name: Optional[str] = None

class GitHubTestResponse(BaseModel):
    """
    Response model for POST /settings/github/test endpoint.
    """
    success: bool
    username: str
    name: str
    avatar: str

class GitHubConnectResponse(BaseModel):
    """
    Response model for POST /settings/github/connect endpoint.
    """
    message: str
    connected: bool
    username: str
    name: str
    avatar_url: str

class GitHubDisconnectResponse(BaseModel):
    """
    Response model for DELETE /settings/github endpoint.
    """
    message: str
    connected: bool
