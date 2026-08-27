from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.api.settings_routes import settings_router
from src.api.project_routes import router as project_router
from src.api.pull_request_routes import router as pull_request_router
from src.api.webhook_routes import router as webhook_router

from src.api.review_routes import router as review_router
from src.api.insights_routes import router as insights_router

app=FastAPI(
    title="AI PR REVIEWER",
    version="1.0.0", 
    description="AI-powered pull request reviewer using the hybrid RAG",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(settings_router)
app.include_router(project_router)
app.include_router(pull_request_router)
app.include_router(webhook_router)
app.include_router(review_router)
app.include_router(insights_router)




    