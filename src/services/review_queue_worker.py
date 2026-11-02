import asyncio
import logging
import os
import socket
from contextlib import suppress
from datetime import datetime, timezone
from uuid import uuid4

from starlette.concurrency import run_in_threadpool

from src.api.auth import get_supabase_client
from src.config import (
    REVIEW_JOB_LEASE_SECONDS,
    REVIEW_JOB_MAX_ATTEMPTS,
    REVIEW_QUEUE_POLL_SECONDS,
    REVIEW_WORKER_CONCURRENCY,
)
from src.services.review_service import review_service
from src.utils.security import sanitize_error_message

logger = logging.getLogger("review_queue_worker")


class ReviewQueueWorker:
    """Poll and process durable review jobs stored in the reviews table."""

    def __init__(self) -> None:
        self.worker_id = f"{socket.gethostname()}:{os.getpid()}:{uuid4().hex[:8]}"
        self._stopping = asyncio.Event()
        self._active_tasks: set[asyncio.Task[None]] = set()

    async def run(self) -> None:
        logger.info(
            "Review queue worker %s started (concurrency cap: %s)",
            self.worker_id,
            REVIEW_WORKER_CONCURRENCY,
        )
        try:
            while not self._stopping.is_set():
                self._active_tasks = {task for task in self._active_tasks if not task.done()}

                while (
                    not self._stopping.is_set()
                    and len(self._active_tasks) < REVIEW_WORKER_CONCURRENCY
                ):
                    try:
                        job = await run_in_threadpool(self._claim_next_job)
                    except Exception as exc:
                        logger.error(
                            "Could not claim a review job: %s",
                            sanitize_error_message(exc),
                        )
                        break

                    if not job:
                        break

                    task = asyncio.create_task(self._process_job(job))
                    self._active_tasks.add(task)

                try:
                    await asyncio.wait_for(
                        self._stopping.wait(),
                        timeout=REVIEW_QUEUE_POLL_SECONDS,
                    )
                except asyncio.TimeoutError:
                    pass
        finally:
            if self._active_tasks:
                # Let claimed jobs finish before closing the client. Their
                # heartbeat tasks keep leases valid during a graceful drain.
                await asyncio.gather(*self._active_tasks, return_exceptions=True)
            logger.info("Review queue worker %s stopped", self.worker_id)

    def stop(self) -> None:
        self._stopping.set()

    def _claim_next_job(self) -> dict | None:
        supabase = get_supabase_client()
        result = supabase.rpc(
            "claim_next_review_job",
            {
                "p_worker_id": self.worker_id,
                "p_max_concurrency": REVIEW_WORKER_CONCURRENCY,
                "p_lease_seconds": REVIEW_JOB_LEASE_SECONDS,
                "p_max_attempts": REVIEW_JOB_MAX_ATTEMPTS,
            },
        ).execute()
        data = result.data or []
        return data[0] if isinstance(data, list) and data else data if isinstance(data, dict) and data else None

    def _heartbeat(self, review_id: str) -> bool:
        supabase = get_supabase_client()
        result = supabase.rpc(
            "heartbeat_review_job",
            {
                "p_review_id": review_id,
                "p_worker_id": self.worker_id,
                "p_lease_seconds": REVIEW_JOB_LEASE_SECONDS,
            },
        ).execute()
        return bool(result.data)

    async def _heartbeat_loop(self, review_id: str, finished: asyncio.Event) -> None:
        interval = max(10, REVIEW_JOB_LEASE_SECONDS // 3)
        while not finished.is_set():
            try:
                await asyncio.wait_for(finished.wait(), timeout=interval)
                return
            except asyncio.TimeoutError:
                pass

            try:
                still_owned = await run_in_threadpool(self._heartbeat, review_id)
            except Exception as exc:
                logger.warning(
                    "Could not renew lease for review %s: %s",
                    review_id,
                    sanitize_error_message(exc),
                )
                continue
            if not still_owned:
                logger.warning("Worker %s lost the lease for review %s", self.worker_id, review_id)
                return

    async def _process_job(self, job: dict) -> None:
        review_id = str(job["id"])
        finished = asyncio.Event()
        heartbeat = asyncio.create_task(self._heartbeat_loop(review_id, finished))
        try:
            await review_service.create_and_execute_review(
                project_id=str(job["project_id"]),
                pr_number=int(job["github_pr_number"]),
                user_id=str(job["created_by"]),
                user_token=None,
                review_id=review_id,
                worker_id=self.worker_id,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(
                "Review worker %s failed job %s: %s",
                self.worker_id,
                review_id,
                sanitize_error_message(exc),
                exc_info=False,
            )
            try:
                await run_in_threadpool(self._mark_failed, review_id, exc)
            except Exception as mark_error:
                logger.error(
                    "Could not persist failure for review %s: %s; the lease will recover it",
                    review_id,
                    sanitize_error_message(mark_error),
                )
        finally:
            finished.set()
            heartbeat.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat

    def _mark_failed(self, review_id: str, error: Exception) -> None:
        safe_error = "Unable to complete AI analysis. " + sanitize_error_message(error)
        supabase = get_supabase_client()
        supabase.table("reviews").update(
            {
                "status": "FAILED",
                "error_message": safe_error,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "worker_id": None,
                "lease_expires_at": None,
            }
        ).eq("id", review_id).eq("worker_id", self.worker_id).execute()
