import asyncio
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from src.services.github_credentials_service import github_credentials_service
from src.services.project_service import ProjectService
from src.services.review_service import ReviewService
from src.utils.security import encryption_service


def test_custom_auth_never_falls_back_to_connected_account():
    with patch.object(github_credentials_service, "get_decrypted_pat") as get_connected_pat:
        with pytest.raises(HTTPException) as exc:
            github_credentials_service.resolve_project_token(
                {"id": "project-1", "auth_type": "custom_token", "custom_token": None},
                user_id="user-1",
                user_token="jwt",
            )

    assert exc.value.status_code == 400
    assert "custom GitHub token" in exc.value.detail
    get_connected_pat.assert_not_called()


def test_custom_auth_resolves_only_its_saved_token():
    custom_token = "ghp_project_specific_token"
    encrypted = encryption_service.encrypt(custom_token)

    with patch.object(github_credentials_service, "get_decrypted_pat") as get_connected_pat:
        token = github_credentials_service.resolve_project_token(
            {"id": "project-1", "auth_type": "custom_token", "custom_token": encrypted},
            user_id="user-1",
            user_token="jwt",
        )

    assert token == custom_token
    get_connected_pat.assert_not_called()


def test_unsupported_auth_mode_fails_closed():
    with patch.object(github_credentials_service, "get_decrypted_pat") as get_connected_pat:
        with pytest.raises(HTTPException) as exc:
            github_credentials_service.resolve_project_token(
                {"id": "project-1", "auth_type": "unexpected", "custom_token": None},
                user_id="user-1",
                user_token="jwt",
            )

    assert exc.value.status_code == 400
    get_connected_pat.assert_not_called()


def test_review_custom_auth_missing_token_fails_with_actionable_error():
    service = ReviewService()
    project = {
        "id": "project-1",
        "user_id": "user-1",
        "auth_type": "custom_token",
        "custom_token": None,
    }

    with patch("src.services.review_service.get_supabase_client") as get_client, \
         patch.object(github_credentials_service, "get_decrypted_pat") as get_connected_pat:
        get_client.return_value.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [project]

        with pytest.raises(HTTPException) as exc:
            service._resolve_project_and_token("project-1", "user-1", "jwt")

    assert exc.value.status_code == 400
    get_connected_pat.assert_not_called()


def test_update_cannot_select_custom_auth_without_a_custom_token():
    async def run():
        service = ProjectService()
        existing = {
            "id": "project-1",
            "user_id": "user-1",
            "github_owner": "acme",
            "github_repository": "repo",
            "auth_type": "connected_account",
            "custom_token": None,
        }

        with patch.object(service, "get_project_by_id", return_value=existing):
            with pytest.raises(HTTPException) as exc:
                await service.update_project(
                    project_id="project-1",
                    user_id="user-1",
                    user_token="jwt",
                    update_data={"auth_type": "custom_token"},
                )

        assert exc.value.status_code == 400
        assert "required" in exc.value.detail

    asyncio.run(run())
