from typing import Optional
from pathlib import Path
from git import Repo
from src.config import REPOSITORIES_DIR

def get_repository_name(repo_url: str) -> str:
    """Extract the repository name from the URL or path."""
    return Path(repo_url.rstrip("/")).stem

def clone_repository(repo_url: str, local_path: Path, token: Optional[str] = None) -> Path:
    """
    Clones a repository using clean HTTPS URL without persisting credentials in .git/config.
    If a token is provided, uses ephemeral http.extraHeader configuration.
    """
    c_opts = [f"http.extraHeader=Authorization: Bearer {token}"] if token else None
    Repo.clone_from(repo_url, local_path, c=c_opts)
    return local_path

def update_repository(local_path: Path, token: Optional[str] = None) -> Path:
    """
    Pulls the latest changes from remote using optional ephemeral authorization header.
    """
    repo = Repo(local_path)
    if token:
        repo.git.pull(c=f"http.extraHeader=Authorization: Bearer {token}")
    else:
        repo.git.pull()
    return local_path

def prepare_repository(repo_url: str, local_path: Optional[Path] = None, token: Optional[str] = None) -> Path:
    """
    Prepares repository directory. If local_path is specified, uses that path (e.g. data/repositories/<user_id>/<project_id>).
    Otherwise falls back to isolated path.
    """
    if local_path:
        target_path = Path(local_path)
    else:
        repo_name = get_repository_name(repo_url)
        target_path = REPOSITORIES_DIR / repo_name

    target_path.parent.mkdir(parents=True, exist_ok=True)

    if (target_path / ".git").exists():
        update_repository(target_path, token=token)
    else:
        clone_repository(repo_url, target_path, token=token)

    return target_path
            

