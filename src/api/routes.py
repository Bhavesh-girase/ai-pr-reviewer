from fastapi import APIRouter,Request

from src.pr_reviewer import PRReviewer
from src.schemas.review import ReviewRequest
from src.schemas.webhook import WebhookRequest
from src.sync.webhook_handler import WebhookHandler

router=APIRouter()

reviewer=PRReviewer()
webhook_handler=WebhookHandler()

@router.get("/health")
def health():
    return {"status":"healthy"}

@router.post("/review-pr")
def review_pull_request(request: ReviewRequest):
    return reviewer.review(
        repo_url=str(request.repo_url),
        owner=request.owner,
        repository=request.repository,
        pull_number=request.pull_number,
    )

@router.post("/webhook")
async def github_webhook(request: Request):
    payload=await request.json()
    return webhook_handler.handle(payload)
    