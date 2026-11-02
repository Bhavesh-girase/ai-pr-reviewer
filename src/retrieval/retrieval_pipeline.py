from pathlib import Path
from langchain_core.documents import Document

from src.ingestion.data_utils import load_chunks

from src.retrieval.loaders import load_vectorstore,load_reranker

from src.retrieval.retrievers import create_bm25,create_hybrid_retriever

from src.retrieval.query_builder import build_search_query

from src.config import TOP_K,RERANK_TOP_K


class RetrievalPipeline:

    def __init__(self, repository_name: str, persist_directory: str | Path | None = None):
        self.repository_name=repository_name

        self.vectorstore=load_vectorstore(repository_name, persist_directory=persist_directory)

        if persist_directory is None:
            # Preserve the legacy cache behavior for standalone/notebook use.
            self.chunks=load_chunks(repository_name)
        else:
            # Project BM25 retrieval must use the same live index that syncs
            # update; a separate pickle snapshot becomes stale after a sync.
            indexed_data = self.vectorstore.get(include=["documents", "metadatas"])
            contents = indexed_data.get("documents") or []
            metadatas = indexed_data.get("metadatas") or []
            self.chunks = [
                Document(
                    page_content=content,
                    metadata=metadatas[index] if index < len(metadatas) and metadatas[index] else {},
                )
                for index, content in enumerate(contents)
                if content is not None
            ]

        self.bm25=create_bm25(self.chunks)

        self.hybrid_retriever=(
            create_hybrid_retriever(
                self.bm25,
                self.vectorstore,
            )
        )
        self.reranker=load_reranker()

    def build_query(self,file_change: dict):
        """ Build a retrieval query"""

        return build_search_query(file_change)

    def retrieve_documents(self, query: str):
        try:
            hybrid_docs = self.hybrid_retriever.invoke(query)

            for doc in hybrid_docs:
                doc.metadata["retrieval_source"] = "Hybrid (BM25 + Vector)"

            return hybrid_docs
        except Exception:
            return []


    def rerank_documents(self, query: str, documents):
        if not documents:
            return []

        pairs = [[query, doc.page_content] for doc in documents]

        scores = self.reranker.predict(pairs)

        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)

        for doc, score in ranked:
            doc.metadata["rerank_score"] = float(score)

        return [doc for doc, score in ranked[:RERANK_TOP_K]]

    def retrieve_context(self, file_change: dict):
        query = self.build_query(file_change)

        documents = self.retrieve_documents(query)

        documents = self.rerank_documents(query, documents)

        return documents
