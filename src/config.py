from dotenv import load_dotenv
from pathlib import Path
import os

# Load root backend environment configuration at initialization
load_dotenv()

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

# Base Paths
# ----------------------------
BASE_DIR = Path("..")

DATA_DIR = BASE_DIR / "data"

DOCS_DIR = DATA_DIR / "docs"

PROCESSED_DIR = DATA_DIR / "processed"

REPOSITORIES_DIR = DATA_DIR / "repositories"

CHROMA_BASE_DIR = DATA_DIR / "chroma"

##########################

TOP_K = 10

HYBRID_WEIGHTS = [0.5, 0.5]

RERANK_TOP_K = 3

# Supabase & Security Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://fltjwocficpdzfuulbxc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", ""))
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

# CORS Configuration
raw_cors = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

# Rate Limiting Configuration
REVIEW_RATE_LIMIT_PER_MINUTE = int(os.getenv("REVIEW_RATE_LIMIT_PER_MINUTE", "10"))

# API Documentation Configuration (Disabled by default in production)
ENABLE_API_DOCS = os.getenv("ENABLE_API_DOCS", "false").lower() == "true"
