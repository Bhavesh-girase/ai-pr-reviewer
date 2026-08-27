import logging
import requests
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "AI-PR-Reviewer-App",
            }
        )
        if token and token.strip():
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {token.strip()}"
                }
            )

    def _handle_response(self, response: requests.Response, operation: str) -> requests.Response:
        """
        Inspects GitHub API response codes and raises sanitized, secure HTTPExceptions.
        Never logs or exposes tokens.
        """
        if response.status_code in [200, 201, 204]:
            return response

        if response.status_code == 401:
            logger.warning(f"GitHub API 401 Unauthorized during {operation}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub authentication failed. Please verify your Personal Access Token."
            )
        elif response.status_code == 403:
            rate_limit_remaining = response.headers.get("x-ratelimit-remaining")
            if rate_limit_remaining == "0":
                logger.warning(f"GitHub API rate limit exceeded during {operation}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="GitHub API rate limit exceeded. Please try again later or verify your token."
                )
            logger.warning(f"GitHub API 403 Forbidden during {operation}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GitHub access forbidden. The provided token does not have access to this repository or webhook scope."
            )
        elif response.status_code == 404:
            logger.warning(f"GitHub resource not found during {operation}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GitHub repository, pull request, or webhook not found."
            )
        elif response.status_code == 422:
            logger.warning(f"GitHub unprocessable entity during {operation}: {response.text[:200]}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"GitHub validation error: {response.text[:200]}"
            )
        elif response.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="GitHub API rate limit exceeded. Please try again later."
            )
        else:
            logger.error(f"GitHub API error {response.status_code} during {operation}: {response.text[:200]}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"GitHub API error: {response.text[:200]}"
            )

    def get_repository(self, owner: str, repository: str) -> Dict[str, Any]:
        """Fetch repository metadata"""
        url = f"{self.BASE_URL}/repos/{owner}/{repository}"
        try:
            response = self.session.get(url, timeout=15)
            self._handle_response(response, f"get_repository {owner}/{repository}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching repository {owner}/{repository}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub API service is currently unreachable."
            )

    def list_pull_requests(
        self,
        owner: str,
        repository: str,
        state: str = "open",
        page: int = 1,
        per_page: int = 20,
        sort: str = "created",
        direction: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        List pull requests for a repository from GitHub REST API.
        state options: 'open', 'closed', 'all'.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repository}/pulls"
        params = {
            "state": state,
            "page": page,
            "per_page": min(per_page, 100),
            "sort": sort,
            "direction": direction
        }
        try:
            response = self.session.get(url, params=params, timeout=20)
            self._handle_response(response, f"list_pull_requests {owner}/{repository}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error listing PRs for {owner}/{repository}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub API service is currently unreachable."
            )

    def get_pull_request(self, owner: str, repository: str, pull_number: int) -> Dict[str, Any]:
        """Fetch single pull request details"""
        url = f"{self.BASE_URL}/repos/{owner}/{repository}/pulls/{pull_number}"
        try:
            response = self.session.get(url, timeout=15)
            self._handle_response(response, f"get_pull_request {owner}/{repository} #{pull_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching PR #{pull_number}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub API service is currently unreachable."
            )

    def get_pull_request_files(self, owner: str, repository: str, pull_number: int) -> List[Dict[str, Any]]:
        """Fetch all files changed in a pull request"""
        url = f"{self.BASE_URL}/repos/{owner}/{repository}/pulls/{pull_number}/files"
        try:
            response = self.session.get(url, params={"per_page": 100}, timeout=20)
            self._handle_response(response, f"get_pull_request_files {owner}/{repository} #{pull_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching files for PR #{pull_number}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub API service is currently unreachable."
            )

    def get_pull_request_diff(self, owner: str, repository: str, pull_number: int) -> str:
        """Fetch the unified diff string for a pull request"""
        url = f"{self.BASE_URL}/repos/{owner}/{repository}/pulls/{pull_number}"
        headers = {"Accept": "application/vnd.github.v3.diff"}
        try:
            response = self.session.get(url, headers=headers, timeout=20)
            self._handle_response(response, f"get_pull_request_diff {owner}/{repository} #{pull_number}")
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching diff for PR #{pull_number}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub API service is currently unreachable."
            )

    # ----------------------------------------------------
    # Phase 4: GitHub Webhook Management Methods
    # ----------------------------------------------------

    def create_webhook(
        self,
        owner: str,
        repository: str,
        webhook_url: str,
        secret: str,
        events: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a webhook on the target GitHub repository for event notifications.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repository}/hooks"
        payload = {
            "name": "web",
            "active": True,
            "events": events or ["pull_request"],
            "config": {
                "url": webhook_url,
                "content_type": "json",
                "secret": secret,
                "insecure_ssl": "0"
            }
        }
        try:
            response = self.session.post(url, json=payload, timeout=20)
            self._handle_response(response, f"create_webhook {owner}/{repository}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error creating webhook for {owner}/{repository}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub API service is currently unreachable."
            )

    def delete_webhook(self, owner: str, repository: str, hook_id: int) -> bool:
        """
        Deletes an existing webhook from GitHub repository.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repository}/hooks/{hook_id}"
        try:
            response = self.session.delete(url, timeout=15)
            if response.status_code == 404:
                # Already deleted or non-existent on GitHub
                return True
            self._handle_response(response, f"delete_webhook {owner}/{repository} #{hook_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error deleting webhook #{hook_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub API service is currently unreachable."
            )

    def get_webhook(self, owner: str, repository: str, hook_id: int) -> Dict[str, Any]:
        """
        Fetches webhook details from GitHub repository.
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repository}/hooks/{hook_id}"
        try:
            response = self.session.get(url, timeout=15)
            self._handle_response(response, f"get_webhook {owner}/{repository} #{hook_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching webhook #{hook_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub API service is currently unreachable."
            )