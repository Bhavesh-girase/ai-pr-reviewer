from typing import Optional
from pathlib import Path
from src.github.repository_manager import prepare_repository
from src.github.github_client import GitHubClient
from src.github.diff_parser import parse_changed_file

from src.ingestion.indexing import build_repository_index
from src.review.review_pipeline import ReviewPipeline
from src.ingestion.index_manager import IndexManager

class PRReviewer:
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.github = GitHubClient(github_token)
        self.index_manager = IndexManager()

    def review(
        self,
        repo_url: str,
        owner: str,
        repository: str,
        pull_number: int,
        local_path: Optional[Path] = None
    ):
        repository_path = prepare_repository(repo_url, local_path=local_path, token=self.github_token)
        repository_name = Path(repository_path).name

        self.index_manager.ensure_index(repository_path)

        files = self.github.get_pull_request_files(owner, repository, pull_number)

        changed_files = []

        for github_file in files:
        
            patch = github_file.get(
                "patch"
            )
        
            if not patch:
                continue
        
            changed_files.append(
                parse_changed_file(
                    github_file
                )
            )
        review_pipeline = ReviewPipeline(repository_name)

        reviews = review_pipeline.review_pull_request(changed_files)

        return reviews
                