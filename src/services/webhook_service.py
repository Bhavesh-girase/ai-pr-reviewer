import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from starlette.concurrency import run_in_threadpool

from src.api.auth import get_supabase_client
from src.security.webhook_signature import verify_github_signature
from src.utils.security import encryption_service
from src.services.pull_request_sync_service import pull_request_sync_service
from src.services.repository_sync_service import repository_sync_service

logger = logging.getLogger(__name__)


async def _execute(query):
    """Execute a synchronous Supabase/PostgREST query outside the event loop."""
    return await run_in_threadpool(query.execute)


class WebhookService:
    """
    Core receiver and verification engine for incoming GitHub Webhook events.
    Enforces replay protection, HMAC-SHA256 signature verification, project resolution,
    and dispatches Pull Request & Repository state synchronizations.
    """

    SUPPORTED_PR_ACTIONS = {
        "opened",
        "reopened",
        "synchronize",
        "closed",
        "edited",
        "ready_for_review",
        "converted_to_draft"
    }
    STALE_DELIVERY_AFTER = timedelta(minutes=30)

    async def handle_webhook(self, raw_body: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
        start_time = time.time()

        # Step 1: Extract and validate required headers
        signature_header = (
            headers.get("x-hub-signature-256")
            or headers.get("X-Hub-Signature-256")
        )
        delivery_id = (
            headers.get("x-github-delivery")
            or headers.get("X-GitHub-Delivery")
        )
        event_type = (
            headers.get("x-github-event")
            or headers.get("X-GitHub-Event")
            or "unknown"
        )

        if not signature_header:
            logger.warning("Rejected webhook request: Missing X-Hub-Signature-256 header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing GitHub webhook signature."
            )

        if not delivery_id:
            logger.warning("Rejected webhook request: Missing X-GitHub-Delivery header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing GitHub delivery ID."
            )

        supabase = await run_in_threadpool(get_supabase_client)

        # Step 3: Parse Payload (JSON) safely
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to parse webhook JSON payload: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed JSON body."
            )

        repo_info = payload.get("repository") or {}
        owner_info = repo_info.get("owner") or {}
        repo_owner = owner_info.get("login") or owner_info.get("name")
        repo_name = repo_info.get("name")

        if not repo_owner or not repo_name:
            logger.warning("Webhook payload missing repository owner or name")
            return {"status": "ignored", "reason": "missing_repository_info"}

        # Step 4: Resolve Project and Verify HMAC-SHA256 Signature
        try:
            projects_res = await _execute(supabase.table("projects")\
                .select("id, default_branch, github_owner, github_repository, webhook_secret_encrypted, webhook_status")\
                .ilike("github_owner", repo_owner)\
                .ilike("github_repository", repo_name))

            candidates = projects_res.data or []
        except Exception as e:
            logger.error(f"Database error resolving project for {repo_owner}/{repo_name}: {str(e)}")
            raise HTTPException(status_code=500, detail="Database lookup error.")

        if not candidates:
            logger.warning(f"No registered project found for repository {repo_owner}/{repo_name}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unregistered repository or invalid signature."
            )

        verified_project = None
        for project in candidates:
            encrypted_secret = project.get("webhook_secret_encrypted")
            if not encrypted_secret:
                continue

            try:
                raw_secret = encryption_service.decrypt(encrypted_secret)
                if verify_github_signature(raw_body, signature_header, raw_secret):
                    verified_project = project
                    break
            except Exception as ex:
                logger.debug(f"Secret decryption/verification failed for candidate project {project['id']}: {str(ex)}")

        if not verified_project:
            logger.warning(f"Signature verification failed for {repo_owner}/{repo_name}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid GitHub webhook signature."
            )

        project_id = verified_project["id"]
        action = payload.get("action")
        now_iso = datetime.now(timezone.utc).isoformat()

        # Claim the unique delivery row before processing. A conditional update
        # lets failed or abandoned deliveries be retried without allowing two
        # simultaneous redeliveries to process the same event.
        delivery_record_id, claimed = await self._claim_delivery(
            supabase=supabase,
            project_id=project_id,
            delivery_id=delivery_id,
            event_type=event_type,
            action=action,
            received_at=now_iso,
        )
        if not claimed:
            logger.info(f"Duplicate webhook delivery ignored: {delivery_id}")
            return {
                "status": "ignored",
                "reason": "duplicate_delivery",
                "delivery_id": delivery_id
            }

        # Step 6: Process Event
        try:
            if event_type == "ping":
                logger.info(f"Received GitHub ping webhook for project {project_id}")
                if delivery_record_id:
                    await _execute(supabase.table("webhook_deliveries").update({
                        "status": "PROCESSED",
                        "processed_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", delivery_record_id))
                return {"status": "pong", "delivery_id": delivery_id, "project_id": project_id}

            elif event_type == "push":
                # Extract branch
                ref = payload.get("ref", "")
                branch_name = ref.replace("refs/heads/", "")
                default_branch = verified_project.get("default_branch") or "main"

                if branch_name != default_branch:
                    logger.info(
                        f"Ignoring push on non-default branch '{branch_name}' for project {project_id} (default: {default_branch})"
                    )
                    if delivery_record_id:
                        await _execute(supabase.table("webhook_deliveries").update({
                            "status": "IGNORED",
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }).eq("id", delivery_record_id))
                    return {"status": "ignored", "reason": "non_default_branch", "branch": branch_name}

                before_commit = payload.get("before")
                after_commit = payload.get("after")
                logger.info(
                    f"Processing push event on default branch '{branch_name}' for project {project_id} "
                    f"({before_commit[:7] if before_commit else ''} -> {after_commit[:7] if after_commit else ''})"
                )

                sync_result = await repository_sync_service.sync_project_repository(
                    project_id=project_id,
                    target_commit=after_commit,
                    base_commit=before_commit
                )

                await _execute(supabase.table("projects").update({
                    "last_webhook_event_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", project_id))

                if delivery_record_id:
                    await _execute(supabase.table("webhook_deliveries").update({
                        "status": "PROCESSED",
                        "processed_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", delivery_record_id))

                duration = round(time.time() - start_time, 3)
                logger.info(f"Successfully processed push event for project {project_id} in {duration}s")

                return {
                    "status": "processed",
                    "delivery_id": delivery_id,
                    "project_id": project_id,
                    "event_type": "push",
                    "branch": branch_name,
                    "sync_result": sync_result,
                    "duration": duration
                }

            elif event_type == "pull_request":
                if action not in self.SUPPORTED_PR_ACTIONS:
                    logger.info(f"Ignoring unsupported pull_request action '{action}' for project {project_id}")
                    if delivery_record_id:
                        await _execute(supabase.table("webhook_deliveries").update({
                            "status": "IGNORED",
                            "processed_at": datetime.now(timezone.utc).isoformat()
                        }).eq("id", delivery_record_id))
                    return {"status": "ignored", "action": action}

                pr_data = payload.get("pull_request") or {}
                pr_number = pr_data.get("number")
                if not pr_number:
                    raise ValueError("pull_request payload missing number")

                logger.info(f"Processing webhook PR event '{action}' for project {project_id} #{pr_number}")

                # Authoritatively sync PR metadata to PostgreSQL
                await run_in_threadpool(
                    pull_request_sync_service.sync_single_pull_request,
                    project_id=project_id,
                    pr_number=pr_number,
                    webhook_pr_data=pr_data,
                    from_webhook=True,
                )

                # Update project last event timestamp
                await _execute(supabase.table("projects").update({
                    "last_webhook_event_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", project_id))

                if delivery_record_id:
                    await _execute(supabase.table("webhook_deliveries").update({
                        "status": "PROCESSED",
                        "processed_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", delivery_record_id))

                duration = round(time.time() - start_time, 3)
                logger.info(f"Successfully processed webhook PR #{pr_number} for project {project_id} in {duration}s")

                return {
                    "status": "processed",
                    "delivery_id": delivery_id,
                    "project_id": project_id,
                    "event_type": event_type,
                    "action": action,
                    "pr_number": pr_number,
                    "duration": duration
                }

            else:
                logger.info(f"Ignoring unhandled GitHub event type '{event_type}'")
                if delivery_record_id:
                    await _execute(supabase.table("webhook_deliveries").update({
                        "status": "IGNORED",
                        "processed_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", delivery_record_id))
                return {"status": "ignored", "event_type": event_type}

        except Exception as e:
            logger.error(f"Error processing webhook event {delivery_id}: {str(e)}", exc_info=True)
            if delivery_record_id:
                try:
                    await _execute(supabase.table("webhook_deliveries").update({
                        "status": "FAILED",
                        "error_message": str(e),
                        "processed_at": datetime.now(timezone.utc).isoformat()
                    }).eq("id", delivery_record_id))
                except Exception:
                    pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Webhook processing failure: {str(e)}"
            )

    async def _claim_delivery(
        self,
        supabase,
        project_id: str,
        delivery_id: str,
        event_type: str,
        action: Optional[str],
        received_at: str,
    ) -> tuple[str, bool]:
        """Atomically insert or reclaim a failed/stale delivery record."""
        delivery_table = supabase.table("webhook_deliveries")
        new_record = {
            "project_id": project_id,
            "delivery_id": delivery_id,
            "event_type": event_type,
            "action": action,
            "received_at": received_at,
            "processed_at": None,
            "status": "PROCESSING",
            "error_message": None,
        }

        try:
            insert_result = await _execute(
                delivery_table.insert(new_record).select("id, status, received_at")
            )
            if insert_result.data:
                return insert_result.data[0]["id"], True
        except Exception as insert_error:
            logger.info(
                "Webhook delivery insert did not claim %s; checking for a prior delivery: %s",
                delivery_id,
                insert_error,
            )

        try:
            existing_result = await _execute(
                delivery_table
                .select("id, project_id, status, received_at")
                .eq("delivery_id", delivery_id)
            )
        except Exception as lookup_error:
            logger.error("Could not verify webhook delivery state for %s: %s", delivery_id, lookup_error)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook delivery state is temporarily unavailable; GitHub may retry.",
                headers={"Retry-After": "30"},
            )

        if not existing_result.data:
            # Never process an event if its idempotency record could not be
            # persisted or verified; returning a 5xx asks GitHub to redeliver.
            logger.error("Could not persist webhook delivery state for %s", delivery_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook delivery state is temporarily unavailable; GitHub may retry.",
                headers={"Retry-After": "30"},
            )

        existing = existing_result.data[0]
        record_id = existing["id"]
        if existing.get("project_id") and existing["project_id"] != project_id:
            return record_id, False

        current_status = str(existing.get("status") or "RECEIVED").upper()
        if current_status in {"PROCESSED", "IGNORED"}:
            return record_id, False

        retry_status = current_status == "FAILED"
        active_status = current_status in {"PROCESSING", "RETRYING", "RECEIVED"}

        if active_status:
            try:
                last_received = existing.get("received_at")
                if isinstance(last_received, datetime):
                    last_received_at = last_received
                elif last_received:
                    last_received_at = datetime.fromisoformat(str(last_received).replace("Z", "+00:00"))
                else:
                    last_received_at = None
                if last_received_at and last_received_at.tzinfo is None:
                    last_received_at = last_received_at.replace(tzinfo=timezone.utc)
                retry_status = bool(
                    last_received_at
                    and datetime.now(timezone.utc) - last_received_at >= self.STALE_DELIVERY_AFTER
                )
            except (TypeError, ValueError):
                retry_status = False

        if not retry_status:
            # The existing attempt is still active. Return a retryable status so
            # GitHub does not permanently acknowledge a delivery that may fail.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook delivery is already being processed; GitHub may retry.",
                headers={"Retry-After": "30"},
            )

        stale_before = (datetime.now(timezone.utc) - self.STALE_DELIVERY_AFTER).isoformat()
        next_status = "RETRYING" if current_status == "PROCESSING" else "PROCESSING"
        claim_query = (
            delivery_table
            .update({
                "status": next_status,
                "received_at": received_at,
                "processed_at": None,
                "error_message": None,
            })
            .eq("id", record_id)
            .eq("status", current_status)
        )
        if active_status:
            claim_query = claim_query.lt("received_at", stale_before)

        claim_result = await _execute(claim_query.select("id"))
        if claim_result.data:
            return record_id, True

        # Another request changed the state first. Leave this request retryable
        # rather than processing the same delivery concurrently.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook delivery is already being processed; GitHub may retry.",
            headers={"Retry-After": "30"},
        )

webhook_service = WebhookService()
