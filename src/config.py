from dotenv import load_dotenv
from pathlib import Path
import os

# Load local development configuration. In Docker, Compose injects values from
# the root .env file into the container environment.
load_dotenv()

# Resolve paths from this file rather than the process working directory. This
# keeps local runs and the /app Docker image on the same persistent data root.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("APP_DATA_DIR", str(BASE_DIR / "data"))).expanduser().resolve()
HF_HOME = os.getenv("HF_HOME", str(DATA_DIR / "huggingface"))
os.environ.setdefault("HF_HOME", HF_HOME)

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

# Initialize local embedding model
try:
    embedding_function = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"local_files_only": True}
    )
except Exception:
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash',
    temperature=0
)

CHUNK_SIZE = 850
CHUNK_OVERLAP = 150

DOCS_DIR = DATA_DIR / "docs"

PROCESSED_DIR = DATA_DIR / "processed"

REPOSITORIES_DIR = DATA_DIR / "repositories"

CHROMA_BASE_DIR = DATA_DIR / "chroma"

##########################

TOP_K = 10

HYBRID_WEIGHTS = [0.5, 0.5]

RERANK_TOP_K = 3

# Supabase & Security Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", ""))
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# CORS Configuration
raw_cors = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

# Rate Limiting Configuration
REVIEW_RATE_LIMIT_PER_MINUTE = int(os.getenv("REVIEW_RATE_LIMIT_PER_MINUTE", "10"))
REVIEW_WORKER_CONCURRENCY = max(1, int(os.getenv("REVIEW_WORKER_CONCURRENCY", "1")))
REVIEW_QUEUE_WORKER_ENABLED = os.getenv("REVIEW_QUEUE_WORKER_ENABLED", "true").lower() == "true"
REVIEW_QUEUE_POLL_SECONDS = max(0.25, float(os.getenv("REVIEW_QUEUE_POLL_SECONDS", "1")))
REVIEW_JOB_LEASE_SECONDS = max(30, int(os.getenv("REVIEW_JOB_LEASE_SECONDS", "180")))
REVIEW_JOB_MAX_ATTEMPTS = max(1, int(os.getenv("REVIEW_JOB_MAX_ATTEMPTS", "3")))
LLM_REQUESTS_PER_MINUTE = max(1, int(os.getenv("LLM_REQUESTS_PER_MINUTE", "10")))

# API Documentation Configuration (Disabled by default in production)
ENABLE_API_DOCS = os.getenv("ENABLE_API_DOCS", "false").lower() == "true"
