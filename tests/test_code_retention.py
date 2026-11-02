from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from src.services.project_service import ProjectService
from src.storage.project_storage import ProjectStorage


def test_project_storage_cleanup_removes_repository_and_index_data():
    with TemporaryDirectory() as temp_dir:
        storage = ProjectStorage(Path(temp_dir))
        repo_dir, chroma_dir = storage.ensure_project_directories("user-1", "project-1")
        (repo_dir / "private_source.py").write_text("secret source", encoding="utf-8")
        (chroma_dir / "private_index.bin").write_bytes(b"private index")

        storage.cleanup_project_storage("user-1", "project-1")

        assert not repo_dir.exists()
        assert not chroma_dir.exists()


def test_project_delete_keeps_database_record_if_local_code_cannot_be_removed():
    service = ProjectService()
    project = {"id": "project-1", "user_id": "user-1"}

    with patch.object(service, "get_project_by_id", return_value=project), \
         patch("src.services.project_service.project_storage.cleanup_project_storage", side_effect=PermissionError("denied")), \
         patch("src.services.project_service.get_supabase_client") as get_client:
        with pytest.raises(HTTPException) as exc:
            service.delete_project("project-1", "user-1", "jwt")

    assert exc.value.status_code == 500
    assert "securely deleted" in exc.value.detail
    get_client.assert_not_called()
