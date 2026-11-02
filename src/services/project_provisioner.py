import logging
from datetime import datetime, timezone
from pathlib import Path
from git import Repo
from langchain_chroma import Chroma
from src.config import embedding_function
from src.utils.security import sanitize_error_message
from src.github.repository_loader import load_repository
from src.ingestion.code_chunker import chunk_documents
from src.github.repository_manager import clone_repository
from src.storage.project_storage import project_storage
from src.services.github_credentials_service import github_credentials_service
from starlette.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)


def _build_project_index(repo_dir: Path, chroma_dir: Path, repository_name: str) -> None:
    documents = load_repository(str(repo_dir))
    chunks = chunk_documents(documents, repository_name=repository_name)
    chunk_ids = [chunk.metadata["chunk_id"] for chunk in chunks if "chunk_id" in chunk.metadata]

    vectorstore = Chroma(
        embedding_function=embedding_function,
        persist_directory=str(chroma_dir),
    )
    if chunks:
        vectorstore.add_documents(documents=chunks, ids=chunk_ids)


def _read_head_commit(repo_dir: Path) -> str:
    return str(Repo(repo_dir).head.commit.hexsha)

class ProjectProvisioner:
    """
    Handles physical workspace provisioning for a Project:
    1. Storage allocation
    2. Git clone with token authentication (without storing credentials in .git/config)
    3. Codebase loading & vector indexing into ChromaDB
    4. HEAD commit hash inspection
    5. Cleanup rollback on failure
    """

    async def provision_project(
        self,
        project_data: dict,
        user_token: str,
        update_status_fn
    ) -> dict:
        project_id = str(project_data["id"])
        user_id = str(project_data["user_id"])
        owner = project_data["github_owner"]
        repo = project_data["github_repository"]
        branch = project_data.get("default_branch") or "main"
        logger.info(f"Starting provisioning for Project {project_id} ({owner}/{repo})")

        # Step 1: Ensure Storage Directories
        repo_dir, chroma_dir = await run_in_threadpool(
            project_storage.ensure_project_directories,
            user_id,
            project_id,
        )

        try:
            # Step 2: Resolve GitHub Token
            token = await run_in_threadpool(
                github_credentials_service.resolve_project_token,
                project_data,
                user_id,
                user_token,
            )

            if not token:
                raise ValueError("No valid GitHub access token available to clone repository.")

            # Step 3: Update Status -> CLONING
            await run_in_threadpool(update_status_fn, project_id, "CLONING")

            # Clean HTTPS clone URL without credentials
            clone_url = f"https://github.com/{owner}/{repo}.git"

            # Clone repository with ephemeral auth header
            logger.info(f"Cloning repository {owner}/{repo} into {repo_dir}")
            await run_in_threadpool(clone_repository, clone_url, repo_dir, token=token)

            # Step 4: Update Status -> INDEXING
            await run_in_threadpool(update_status_fn, project_id, "INDEXING")

            # Load and chunk documents
            logger.info(f"Loading repository source documents from {repo_dir}")
            # Build Chroma vectorstore inside project storage directory
            logger.info(f"Indexing repository {owner}/{repo} into ChromaDB at {chroma_dir}")
            await run_in_threadpool(_build_project_index, repo_dir, chroma_dir, repo)

            # Step 5: Read HEAD Commit Hash
            commit_hash = await run_in_threadpool(_read_head_commit, repo_dir)
            now_iso = datetime.now(timezone.utc).isoformat()

            # Step 6: Mark READY
            final_update = {
                "status": "READY",
                "clone_path": str(repo_dir),
                "chroma_path": str(chroma_dir),
                "current_commit_hash": commit_hash,
                "last_indexed_at": now_iso,
                "last_synced_at": now_iso,
                "error_message": None
            }
            logger.info(f"Successfully provisioned Project {project_id} (Commit: {commit_hash[:7]})")

            # Step 7: Trigger Webhook Registration (Non-blocking failure)
            try:
                from src.services.webhook_registration_service import webhook_registration_service
                await webhook_registration_service.register_webhook(project_id, user_id, user_token)
            except Exception as whex:
                logger.warning(f"Initial webhook registration skipped or failed for {project_id}: {str(whex)}")

            return final_update

        except Exception as e:
            sanitized_err = sanitize_error_message(str(e))
            err_msg = f"Provisioning failed for project {project_id}: {sanitized_err}"
            logger.error(err_msg, exc_info=False)

            # Best-effort rollback while preserving the original provisioning
            # failure; cleanup itself reports failures for operational follow-up.
            cleanup_failed = False
            try:
                await run_in_threadpool(project_storage.cleanup_project_storage, user_id, project_id)
            except Exception as cleanup_error:
                logger.error(f"Provisioning rollback cleanup failed for {project_id}: {cleanup_error}")
                cleanup_failed = True

            # Mark DB FAILED with sanitized error
            public_error = sanitized_err
            if cleanup_failed:
                public_error += " Local repository cleanup also failed; retry project deletion or contact support."
            failed_update = {
                "status": "FAILED",
                "error_message": public_error
            }
            return failed_update

project_provisioner = ProjectProvisioner()
