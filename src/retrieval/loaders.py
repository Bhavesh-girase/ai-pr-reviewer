from langchain_chroma import Chroma
from sentence_transformers import CrossEncoder

from src.config import embedding_function
from src.ingestion.data_utils import get_chroma_directory


def load_vectorstore(repository_name: str):
    return Chroma(
        persist_directory=str(
            get_chroma_directory(repository_name)
        ),
        embedding_function=embedding_function
    )


# Load once per Python process/module lifecycle.
reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def load_reranker():
    return reranker
