from langchain_chroma import Chroma
from src.config import embedding_function
from dotenv import load_dotenv
from sentence_transformers import CrossEncoder
from src.ingestion.data_utils import get_chroma_directory

load_dotenv()

def load_vectorstore(repository_name: str):
    return Chroma(
        persist_directory=str(
            get_chroma_directory(repository_name)
        ),
        embedding_function=embedding_function
    )

def load_reranker():
    return CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ) 
