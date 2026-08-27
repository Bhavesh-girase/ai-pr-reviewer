import asyncio
import logging
import os
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from fastapi import HTTPException, status
from git import Repo

from src.api.auth import get_supabase_client
from src.services.project_service import project_service
from src.services.github_credentials_service import github_credentials_service
from src.storage.project_storage import project_storage
from src.sync.incremental_indexer import IncrementalIndexer

logger = logging.getLogger(__name__)

class RepositorySyncService:
    """
    Master orchestrator for automatic and manual repository synchronization.
    Maintains Git working tree and ChromaDB vector index consistency across commit updates.
    """

    def __init__(self):
        # Per-project concurrency locks
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def _resolve_project_and_token(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        user_token: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        supabase = get_supabase_client(user_token)
        res = supabase.table("projects").select("*").eq("id", project_id).execute()
        if not res.data or len(res.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found."
            )
        project = res.data[0]
        target_user_id = user_id or project["user_id"]

        auth_type = project.get("auth_type", "connected_account")
        custom_token = project.get("custom_token")

        token = None
        if auth_type == "custom_token" and custom_token:
            token = custom_token.strip()
        else:
            token = github_credentials_service.get_decrypted_pat(target_user_id, user_token)

        return project, token

    def _detect_git_changes(
        self,
        repo_path: Path,
        old_commit: str,
        new_commit: str
    ) -> Tuple[List[str], List[str], List[str], List[Tuple[str, str]]]:
        """
        Runs `git diff --name-status old_commit new_commit` and categorizes changes into:
        (added, modified, deleted, renamed)
        """
        added_files: List[str] = []
        modified_files: List[str] = []
        deleted_files: List[str] = []
        renamed_files: List[Tuple[str, str]] = []

        try:
            cmd = ["git", "diff", "--name-status", old_commit, new_commit]
            result = subprocess.run(
                cmd,
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.splitlines():
                parts = line.strip().split("\t")
                if not parts or not parts[0]:
                    continue
                status_code = parts[0]

                if status_code.startswith("A") and len(parts) >= 2:
                    added_files.append(parts[1])
                elif status_code.startswith("M") and len(parts) >= 2:
                    modified_files.append(parts[1])
                elif status_code.startswith("D") and len(parts) >= 2:
                    deleted_files.append(parts[1])
                elif status_code.startswith("R") and len(parts) >= 3:
                    renamed_files.append((parts[1], parts[2]))
                elif len(parts) >= 2:
                    # Generic fallback
                    modified_files.append(parts[1])

        except Exception as e:
            logger.warning(f"Git diff failed between {old_commit[:7]} and {new_commit[:7]}: {str(e)}")
            # If diff between commits fails (e.g. shallow clone or orphan branch), fall back to re-indexing all
            pass

        return added_files, modified_files, deleted_files, renamed_files

    async def sync_project_repository(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        user_token: Optional[str] = None,
        target_commit: Optional[str] = None,
        base_commit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes full repository and ChromaDB index synchronization.
        Thread-safe and concurrency-protected per project.
        """
        lock = self._locks[project_id]

        async with lock:
            start_time = time.time()
            supabase = get_supabase_client(user_token)

            # Step 1: Mark sync_status = SYNCING
            now_iso = datetime.now(timezone.utc).isoformat()
            supabase.table("projects").update({
                "sync_status": "SYNCING",
                "last_sync_started_at": now_iso,
                "sync_error_message": None
            }).eq("id", project_id).execute()

            try:
                # Step 2: Resolve Project and Token
                project, token = self._resolve_project_and_token(project_id, user_id, user_token)
                owner = project["github_owner"]
                repo_name = project["github_repository"]
                branch = project.get("default_branch") or "main"
                user_uuid = project["user_id"]

                repo_dir, chroma_dir = project_storage.ensure_project_directories(user_uuid, project_id)
                repo_path = Path(project.get("clone_path") or str(repo_dir))
                chroma_path = Path(project.get("chroma_path") or str(chroma_dir))

                # Step 3: Ensure local clone exists
                auth_url = (
                    f"https://x-access-token:{token}@github.com/{owner}/{repo_name}.git"
                    if token else f"https://github.com/{owner}/{repo_name}.git"
                )

                if not (repo_path / ".git").exists():
                    logger.info(f"Cloning missing repository workspace for project {project_id}")
                    Repo.clone_from(auth_url, repo_path)

                git_repo = Repo(repo_path)

                # Set origin URL with authenticated token
                if "origin" in [remote.name for remote in git_repo.remotes]:
                    git_repo.remotes.origin.set_url(auth_url)
                else:
                    git_repo.create_remote("origin", auth_url)

                # Step 4: Fetch remote branch
                logger.info(f"Fetching latest changes for {owner}/{repo_name} (branch: {branch})")
                git_repo.remotes.origin.fetch(branch)

                # Step 5: Determine old and new commit hashes
                old_commit = (
                    base_commit
                    or project.get("current_commit_hash")
                    or str(git_repo.head.commit.hexsha)
                )

                # Remote latest commit
                remote_ref = git_repo.remotes.origin.refs[branch]
                new_commit = target_commit or str(remote_ref.commit.hexsha)

                logger.info(f"Project {project_id} sync commits: {old_commit[:7]} -> {new_commit[:7]}")

                # If commit hash is identical, repository is already synchronized
                if old_commit == new_commit and project.get("current_commit_hash") == new_commit:
                    logger.info(f"Project {project_id} repository already up-to-date at commit {new_commit[:7]}")
                    now_done = datetime.now(timezone.utc).isoformat()
                    supabase.table("projects").update({
                        "sync_status": "READY",
                        "last_synced_at": now_done,
                        "last_sync_completed_at": now_done,
                        "sync_error_message": None
                    }).eq("id", project_id).execute()

                    return {
                        "status": "READY",
                        "current_commit": new_commit,
                        "last_synced_at": now_done,
                        "last_indexed_at": project.get("last_indexed_at"),
                        "changed_files_count": 0,
                        "message": "Repository is already synchronized with latest commit."
                    }

                # Step 6: Detect changed files between commits
                added, modified, deleted, renamed = self._detect_git_changes(repo_path, old_commit, new_commit)
                total_changes = len(added) + len(modified) + len(deleted) + len(renamed)

                # Step 7: Update local working tree to new commit
                git_repo.git.checkout(branch)
                git_repo.git.reset("--hard", f"origin/{branch}")

                # Step 8: Trigger Incremental Indexer on ChromaDB
                indexer = IncrementalIndexer(
                    repository_name=repo_name,
                    persist_directory=str(chroma_path)
                )

                if total_changes > 0:
                    logger.info(f"Applying incremental index updates ({total_changes} files)")
                    indexer.sync_changes(
                        repository_path=str(repo_path),
                        added_files=added,
                        modified_files=modified,
                        deleted_files=deleted,
                        renamed_files=renamed
                    )
                else:
                    # Fallback if diff was empty but commit changed: re-index full repository safely
                    from src.github.repository_loader import load_repository
                    from src.ingestion.code_chunker import chunk_documents
                    docs = load_repository(str(repo_path))
                    chunks = chunk_documents(docs, repository_name=repo_name)
                    chunk_ids = [c.metadata["chunk_id"] for c in chunks if "chunk_id" in c.metadata]
                    if chunks:
                        indexer.vectorstore.add_documents(documents=chunks, ids=chunk_ids)

                # Step 9: Atomically update database metadata to READY
                now_completed = datetime.now(timezone.utc).isoformat()
                final_update = {
                    "current_commit_hash": new_commit,
                    "last_indexed_at": now_completed,
                    "last_synced_at": now_completed,
                    "last_sync_completed_at": now_completed,
                    "sync_status": "READY",
                    "status": "READY",
                    "sync_error_message": None,
                    "error_message": None
                }
                supabase.table("projects").update(final_update).eq("id", project_id).execute()

                duration = round(time.time() - start_time, 2)
                logger.info(
                    f"Successfully synchronized Project {project_id} to commit {new_commit[:7]} "
                    f"({total_changes} files changed) in {duration}s"
                )

                return {
                    "status": "READY",
                    "current_commit": new_commit,
                    "last_synced_at": now_completed,
                    "last_indexed_at": now_completed,
                    "changed_files_count": total_changes,
                    "message": f"Successfully synchronized {total_changes} changed files to commit {new_commit[:7]}."
                }

            except Exception as e:
                err_msg = f"Repository synchronization failed: {str(e)}"
                logger.error(err_msg, exc_info=True)

                # Rollback: Mark sync_status = SYNC_FAILED, keep previous commit intact
                now_failed = datetime.now(timezone.utc).isoformat()
                try:
                    supabase.table("projects").update({
                        "sync_status": "SYNC_FAILED",
                        "sync_error_message": str(e),
                        "last_sync_completed_at": now_failed
                    }).eq("id", project_id).execute()
                except Exception:
                    pass

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=err_msg
                )

    def get_sync_status(
        self,
        project_id: str,
        user_id: Optional[str] = None,
        user_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves real-time sync state for a project.
        """
        project, _ = self._resolve_project_and_token(project_id, user_id, user_token)
        sync_status = project.get("sync_status", "READY")
        is_syncing = (sync_status == "SYNCING")

        return {
            "project_id": project_id,
            "status": project.get("status", "READY"),
            "sync_status": sync_status,
            "current_commit_hash": project.get("current_commit_hash"),
            "last_synced_at": project.get("last_synced_at"),
            "last_indexed_at": project.get("last_indexed_at"),
            "last_sync_started_at": project.get("last_sync_started_at"),
            "last_sync_completed_at": project.get("last_sync_completed_at"),
            "sync_error_message": project.get("sync_error_message"),
            "is_syncing": is_syncing
        }

repository_sync_service = RepositorySyncService()
