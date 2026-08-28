from pathlib import Path
import time

from src.github.repository_manager import prepare_repository
from src.github.github_client import GitHubClient
from src.github.diff_parser import parse_changed_file

from src.ingestion.index_manager import IndexManager

from src.review.review_pipeline import ReviewPipeline


class PRReviewer:
    """
    Main orchestrator for the AI PR Reviewer.

    Responsibilities:
    - Prepare the repository
    - Ensure the repository is indexed
    - Fetch pull request files
    - Parse changed files
    - Generate AI reviews
    """

    def __init__(self, github_token: str | None = None):
        self.github_token = github_token
        self.github = GitHubClient(github_token)
        self.index_manager = IndexManager()

    def review(
        self,
        repo_url: str,
        owner: str,
        repository: str,
        pull_number: int,
        local_path: Path | None = None,
    ):
        start_time = time.time()
        # --------------------------------------------------
        # Step 1 : Clone / Update repository
        # --------------------------------------------------

        repository_path = prepare_repository(repo_url, local_path=local_path, token=self.github_token)
        repository_name = Path(repository_path).name

        # --------------------------------------------------
        # Step 2 : Ensure repository index exists
        # --------------------------------------------------

        self.index_manager.ensure_index(repository_path)

        # --------------------------------------------------
        # Step 3 : Fetch changed files and PR details from GitHub
        # --------------------------------------------------

        pr_details = self.github.get_pull_request(
            owner=owner,
            repository=repository,
            pull_number=pull_number,
        )
        base_sha = pr_details["base"]["sha"]
        head_sha = pr_details["head"]["sha"]

        github_files = self.github.get_pull_request_files(
            owner=owner,
            repository=repository,
            pull_number=pull_number,
        )

        # --------------------------------------------------
        # Step 4 : Parse patches and retrieve base/head code
        # --------------------------------------------------

        from git import Repo
        repo = Repo(repository_path)
        
        # Ensure we have the PR commits locally
        try:
            if self.github_token:
                repo.git.fetch("origin", f"pull/{pull_number}/head", c=f"http.extraHeader=Authorization: Bearer {self.github_token}")
            else:
                repo.remotes.origin.fetch(f"pull/{pull_number}/head")
        except Exception as e:
            print(f"Warning: Failed to fetch PR commits: {e}")

        changed_files = []

        for github_file in github_files:
            patch = github_file.get("patch")

            # Skip binary files or files without patch
            if not patch:
                continue

            filename = github_file["filename"]
            
            # Retrieve original (base) and modified (head) contents
            try:
                original_code = repo.git.show(f"{base_sha}:{filename}")
            except Exception:
                original_code = ""

            try:
                modified_code = repo.git.show(f"{head_sha}:{filename}")
            except Exception:
                modified_code = ""

            file_change = parse_changed_file(github_file)
            file_change["original_code"] = original_code
            file_change["modified_code"] = modified_code
            changed_files.append(file_change)

        # --------------------------------------------------
        # Step 5 : Review the pull request
        # --------------------------------------------------

        review_pipeline = ReviewPipeline(repository_name)

        reviews, total_chunks = review_pipeline.review_pull_request(
            changed_files
        )

        duration = round(time.time() - start_time, 2)

        return {
            "reviews": reviews,
            "metadata": {
                "duration": duration,
                "llm": "Gemini 2.5 Flash",
                "chunks_retrieved": total_chunks,
                "repository": repository,
                "base_branch": pr_details["base"]["ref"],
                "head_branch": pr_details["head"]["ref"],
                "confidence": 92
            }
        }