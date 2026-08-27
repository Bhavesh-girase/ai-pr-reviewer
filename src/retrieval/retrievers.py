from langchain_community.retrievers import BM25Retriever
from src.config import TOP_K,HYBRID_WEIGHTS

def create_bm25(chunks,k=TOP_K):
    retriever=BM25Retriever.from_documents(chunks)
    retriever.k=k
    return retriever

from langchain_classic.retrievers import EnsembleRetriever

def create_hybrid_retriever(
        bm25,
        vectorstore,
        k=TOP_K,
        weights=None
):
    if weights is None:
        weights = HYBRID_WEIGHTS

    vector = vectorstore.as_retriever(
        search_kwargs={"k": k}
    )

    return EnsembleRetriever(
        retrievers=[bm25, vector],
        weights=weights
    )

   