import logging
from datetime import datetime, timezone
from pathlib import Path
from git import Repo
from langchain_chroma import Chroma
from src.config import embedding_function
from src.github.repository_loader import load_repository
from src.ingestion.code_chunker import chunk_documents
from src.github.repository_manager import clone_repository
from src.storage.project_storage import project_storage
from src.services.github_credentials_service import github_credentials_service

logger = logging.getLogger(__name__)

class ProjectProvisioner:
    """
    Handles physical workspace provisioning for a Project:
    1. Storage allocation
    2. Git clone with token authentication
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
        auth_type = project_data.get("auth_type", "connected_account")
        custom_token = project_data.get("custom_token")

        logger.info(f"Starting provisioning for Project {project_id} ({owner}/{repo})")

        # Step 1: Ensure Storage Directories
        repo_dir, chroma_dir = project_storage.ensure_project_directories(user_id, project_id)

        try:
            # Step 2: Resolve GitHub Token
            token = None
            if auth_type == "custom_token" and custom_token:
                token = custom_token.strip()
            else:
                token = github_credentials_service.get_decrypted_pat(user_id, user_token)

            if not token:
                raise ValueError("No valid GitHub access token available to clone repository.")

            # Step 3: Update Status -> CLONING
            update_status_fn(project_id, "CLONING")

            # Format authenticated git URL
            clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"

            # Clone repository
            logger.info(f"Cloning repository {owner}/{repo} into {repo_dir}")
            clone_repository(clone_url, repo_dir)

            # Step 4: Update Status -> INDEXING
            update_status_fn(project_id, "INDEXING")

            # Load and chunk documents
            logger.info(f"Loading repository source documents from {repo_dir}")
            documents = load_repository(str(repo_dir))
            chunks = chunk_documents(documents, repository_name=repo)
            chunk_ids = [chunk.metadata["chunk_id"] for chunk in chunks if "chunk_id" in chunk.metadata]

            # Build Chroma vectorstore inside project storage directory
            logger.info(f"Persisting {len(chunks)} vector embeddings to ChromaDB at {chroma_dir}")
            vectorstore = Chroma(
                embedding_function=embedding_function,
                persist_directory=str(chroma_dir)
            )
            if chunks:
                vectorstore.add_documents(documents=chunks, ids=chunk_ids)

            # Step 5: Read HEAD Commit Hash
            git_repo = Repo(repo_dir)
            commit_hash = str(git_repo.head.commit.hexsha)
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
            err_msg = f"Provisioning failed for project {project_id}: {str(e)}"
            logger.error(err_msg, exc_info=True)

            # Rollback: Clean storage directories
            project_storage.cleanup_project_storage(user_id, project_id)

            # Mark DB FAILED
            failed_update = {
                "status": "FAILED",
                "error_message": str(e)
            }
            return failed_update

project_provisioner = ProjectProvisioner()
