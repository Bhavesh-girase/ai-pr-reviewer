import shutil
import logging
from pathlib import Path
from src.config import BASE_DIR

logger = logging.getLogger(__name__)

class ProjectStorage:
    """
    Manages local filesystem workspace allocation and cleanup for multi-user project resources.
    Storage Layout:
    storage/users/{user_uuid}/repositories/{project_uuid}/
    storage/users/{user_uuid}/chroma/{project_uuid}/
    """

    def __init__(self, base_storage_dir: Path = None):
        self.base_dir = base_storage_dir or (BASE_DIR / "storage")

    def get_user_dir(self, user_id: str) -> Path:
        return self.base_dir / "users" / str(user_id)

    def get_repository_dir(self, user_id: str, project_id: str) -> Path:
        return self.get_user_dir(user_id) / "repositories" / str(project_id)

    def get_chroma_dir(self, user_id: str, project_id: str) -> Path:
        return self.get_user_dir(user_id) / "chroma" / str(project_id)

    def ensure_project_directories(self, user_id: str, project_id: str) -> tuple[Path, Path]:
        """
        Creates repository and Chroma storage directories for the given project UUID.
        Returns (repo_path, chroma_path).
        """
        repo_dir = self.get_repository_dir(user_id, project_id)
        chroma_dir = self.get_chroma_dir(user_id, project_id)

        repo_dir.mkdir(parents=True, exist_ok=True)
        chroma_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Ensured project workspace storage paths: Repo={repo_dir}, Chroma={chroma_dir}")
        return repo_dir, chroma_dir

    def cleanup_project_storage(self, user_id: str, project_id: str) -> None:
        """
        Recursively deletes local clone and Chroma vector storage for a project.
        """
        repo_dir = self.get_repository_dir(user_id, project_id)
        chroma_dir = self.get_chroma_dir(user_id, project_id)

        if repo_dir.exists():
            try:
                shutil.rmtree(repo_dir, ignore_errors=True)
                logger.info(f"Deleted repository storage directory: {repo_dir}")
            except Exception as e:
                logger.error(f"Error removing repo dir {repo_dir}: {str(e)}")

        if chroma_dir.exists():
            try:
                shutil.rmtree(chroma_dir, ignore_errors=True)
                logger.info(f"Deleted Chroma storage directory: {chroma_dir}")
            except Exception as e:
                logger.error(f"Error removing chroma dir {chroma_dir}: {str(e)}")

project_storage = ProjectStorage()
