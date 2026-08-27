import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from src.api.auth import get_supabase_client
from src.github.github_client import GitHubClient
from src.services.github_credentials_service import github_credentials_service
from src.services.project_provisioner import project_provisioner
from src.storage.project_storage import project_storage

logger = logging.getLogger(__name__)

class ProjectService:
    """
    Database & business orchestration service managing public.projects in Supabase PostgreSQL.
    All operations are scoped to user_token so Supabase RLS enforces auth.uid() = user_id.
    """

    TABLE_NAME = "projects"

    def _handle_db_error(self, e: Exception, operation: str) -> None:
        err_msg = str(e)
        logger.error(f"Database error during {operation}: {err_msg}")
        if "relation" in err_msg and "does not exist" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database Error: Table 'public.projects' does not exist in Supabase. Please execute the SQL migration script."
            )
        elif "permission denied" in err_msg.lower() or "row-level security" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Database Error: Permission denied by Supabase Row Level Security (RLS)."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database failure during {operation}: {err_msg}"
            )

    def _get_github_client_for_user(self, user_id: str, user_token: str, auth_type: str, custom_token: Optional[str]) -> GitHubClient:
        token = None
        if auth_type == "custom_token" and custom_token:
            token = custom_token.strip()
        else:
            token = github_credentials_service.get_decrypted_pat(user_id, user_token)
        return GitHubClient(token=token)

    def get_user_projects(self, user_id: str, user_token: str) -> List[Dict[str, Any]]:
        try:
            supabase = get_supabase_client(user_token)
            res = supabase.table(self.TABLE_NAME).select("*").order("created_at", desc=True).execute()
            return res.data or []
        except HTTPException:
            raise
        except Exception as e:
            self._handle_db_error(e, "fetch user projects")
            return []

    def get_project_by_id(self, project_id: str, user_id: str, user_token: str) -> Dict[str, Any]:
        try:
            supabase = get_supabase_client(user_token)
            res = supabase.table(self.TABLE_NAME).select("*").eq("id", project_id).execute()
            if not res.data or len(res.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project with ID '{project_id}' not found."
                )
            return res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            self._handle_db_error(e, f"fetch project {project_id}")
            return {}

    async def create_project(self, user_id: str, user_token: str, input_data: dict) -> Dict[str, Any]:
        owner = input_data["github_owner"].strip()
        repo = input_data["github_repository"].strip()
        auth_type = input_data.get("auth_type", "connected_account")
        custom_token = input_data.get("custom_token")

        # Step 1: Validate repository existence with GitHub API
        gh_client = self._get_github_client_for_user(user_id, user_token, auth_type, custom_token)
        try:
            repo_info = gh_client.get_repository(owner, repo)
            default_branch = input_data.get("default_branch") or repo_info.get("default_branch") or "main"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub validation failed for repository '{owner}/{repo}': {str(e)}"
            )

        # Step 2: Insert initial DB record with status = CREATING
        db_payload = {
            "user_id": user_id,
            "project_name": input_data["project_name"].strip(),
            "github_owner": owner,
            "github_repository": repo,
            "default_branch": default_branch,
            "auth_type": auth_type,
            "custom_token": custom_token,
            "status": "CREATING"
        }

        supabase = get_supabase_client(user_token)
        try:
            res = supabase.table(self.TABLE_NAME).insert(db_payload).execute()
            if not res.data or len(res.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to insert project record into database."
                )
            project_record = res.data[0]
        except HTTPException:
            raise
        except Exception as e:
            self._handle_db_error(e, "insert initial project record")
            return {}

        project_id = project_record["id"]

        # Helper status updater for provisioner
        def update_status(pid: str, new_status: str):
            try:
                supabase.table(self.TABLE_NAME).update({"status": new_status}).eq("id", pid).execute()
            except Exception as ex:
                logger.error(f"Status update failure for {pid} -> {new_status}: {str(ex)}")

        # Step 3: Run Project Provisioner
        provision_res = await project_provisioner.provision_project(
            project_record,
            user_token,
            update_status
        )

        # Step 4: Update final status & paths in DB
        try:
            final_res = supabase.table(self.TABLE_NAME).update(provision_res).eq("id", project_id).execute()
            return final_res.data[0] if final_res.data else project_record
        except Exception as e:
            self._handle_db_error(e, "update provisioned project state")
            return project_record

    async def update_project(self, project_id: str, user_id: str, user_token: str, update_data: dict) -> Dict[str, Any]:
        existing = self.get_project_by_id(project_id, user_id, user_token)

        new_owner = update_data.get("github_owner") or existing["github_owner"]
        new_repo = update_data.get("github_repository") or existing["github_repository"]
        repo_changed = (new_owner != existing["github_owner"] or new_repo != existing["github_repository"])

        payload = {k: v for k, v in update_data.items() if v is not None}

        supabase = get_supabase_client(user_token)
        try:
            res = supabase.table(self.TABLE_NAME).update(payload).eq("id", project_id).execute()
            updated_record = res.data[0] if res.data else existing
        except Exception as e:
            self._handle_db_error(e, f"update project {project_id}")
            return existing

        # If repo changed, re-provision workspace
        if repo_changed:
            project_storage.cleanup_project_storage(user_id, project_id)

            def update_status(pid: str, new_status: str):
                supabase.table(self.TABLE_NAME).update({"status": new_status}).eq("id", pid).execute()

            provision_res = await project_provisioner.provision_project(
                updated_record,
                user_token,
                update_status
            )
            final_res = supabase.table(self.TABLE_NAME).update(provision_res).eq("id", project_id).execute()
            return final_res.data[0] if final_res.data else updated_record

        return updated_record

    def delete_project(self, project_id: str, user_id: str, user_token: str) -> Dict[str, Any]:
        # Verify ownership first
        self.get_project_by_id(project_id, user_id, user_token)

        supabase = get_supabase_client(user_token)
        try:
            supabase.table(self.TABLE_NAME).delete().eq("id", project_id).execute()
        except Exception as e:
            self._handle_db_error(e, f"delete project {project_id}")

        # Delete local clone and Chroma directories
        project_storage.cleanup_project_storage(user_id, project_id)

        return {"message": f"Project '{project_id}' and storage resources deleted successfully."}

project_service = ProjectService()
