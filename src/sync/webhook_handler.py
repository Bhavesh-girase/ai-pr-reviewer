from src.github.repository_manager import prepare_repository
from src.sync.repository_updater import RepositoryUpdater

class WebhookHandler:

    def __init__(self):
        pass

    def handle(self,payload: dict):
        action=payload.get("action")

        merged=(payload.get("pull_request",{}).get("merged",False))

        if action !="closed":
            return 
            
        if not merged:
            return 

        repo_url=(payload["repository"]["clone_url"])

        repository_path=prepare_repository(repo_url)

        RepositoryUpdater(repository_path).synchronize()

        