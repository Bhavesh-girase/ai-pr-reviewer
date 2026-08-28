from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.config import CORS_ALLOWED_ORIGINS, ENABLE_API_DOCS
from src.api.routes import router
from src.api.settings_routes import settings_router
from src.api.project_routes import router as project_router
from src.api.pull_request_routes import router as pull_request_router
from src.api.webhook_routes import router as webhook_router

from src.api.review_routes import router as review_router
from src.api.insights_routes import router as insights_router

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app = FastAPI(
    title="AI PR REVIEWER",
    version="1.0.0", 
    description="AI-powered pull request reviewer using the hybrid RAG",
    docs_url="/docs" if ENABLE_API_DOCS else None,
    redoc_url="/redoc" if ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_API_DOCS else None,
)

# Add Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Enable CORS for explicit allowed frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
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




    