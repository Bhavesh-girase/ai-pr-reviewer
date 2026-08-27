from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI
from pathlib import Path

# pip install sentence-transformers langchain-huggingface
from langchain_huggingface import HuggingFaceEmbeddings

# This downloads a small, highly effective open-source model to your machine
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")



load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / "frontend" / ".env")



llm=ChatGoogleGenerativeAI(
    model='gemini-2.5-flash',
    temperature=0
)

CHUNK_SIZE=850
CHUNK_OVERLAP=150

# Base Paths
# ----------------------------
BASE_DIR = Path("..")

DATA_DIR = BASE_DIR / "data"

DOCS_DIR = DATA_DIR / "docs"

PROCESSED_DIR = DATA_DIR / "processed"

REPOSITORIES_DIR=DATA_DIR / "repositories"

CHROMA_BASE_DIR=DATA_DIR / "chroma"

##########################


TOP_K = 10

HYBRID_WEIGHTS = [0.5, 0.5]

RERANK_TOP_K = 3

# Supabase & Security Configuration
import os
SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("VITE_SUPABASE_URL", "https://fltjwocficpdzfuulbxc.supabase.co"))
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_KEY", os.getenv("VITE_SUPABASE_ANON_KEY", "")))
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")

