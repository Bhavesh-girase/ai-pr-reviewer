from pathlib import Path
from git import Repo
from src.config import REPOSITORIES_DIR

def get_repository_name(repo_url:str):
    """ extract the repo name from the url"""
    return Path(repo_url.rstrip("/")).stem

def clone_repository(repo_url:str,local_path: Path):
    """ clone repo"""
    Repo.clone_from(repo_url,local_path)
    return local_path

def update_repository(local_path: Path):
    """pull the latest changes from the remote repo"""
    repo=Repo(local_path)
    repo.remotes.origin.pull()

    return local_path
    

def prepare_repository(repo_url: str):
    """ clone the repo if it does not exist
    otherwise pull the latest changes
    """

    repo_name=get_repository_name(repo_url)
    local_repo=REPOSITORIES_DIR / repo_name

    REPOSITORIES_DIR.mkdir(parents=True,exist_ok=True)

    if local_repo.exists():
        print(f"Updating {repo_name}...")
        update_repository(local_repo)

    else :
        print(f"Cloning {repo_name}....")

        clone_repository(repo_url,local_repo)

    return local_repo
            

