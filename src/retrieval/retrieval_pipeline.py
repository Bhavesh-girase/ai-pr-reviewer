from src.ingestion.data_utils import load_chunks

from src.retrieval.loaders import load_vectorstore,load_reranker

from src.retrieval.retrievers import create_bm25,create_hybrid_retriever

from src.retrieval.query_builder import build_search_query

from src.config import TOP_K,RERANK_TOP_K


class RetrievalPipeline:

    def __init__(self,repository_name: str):
        self.repository_name=repository_name

        self.chunks=load_chunks(repository_name)

        self.vectorstore=load_vectorstore(repository_name)

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
            bm25_docs = self.bm25.invoke(query)
            bm25_ids = {doc.metadata.get("chunk_id") for doc in bm25_docs if "chunk_id" in doc.metadata}
        except Exception:
            bm25_ids = set()

        try:
            vector_retriever = self.vectorstore.as_retriever(search_kwargs={"k": TOP_K})
            vector_docs = vector_retriever.invoke(query)
            vector_ids = {doc.metadata.get("chunk_id") for doc in vector_docs if "chunk_id" in doc.metadata}
        except Exception:
            vector_ids = set()

        hybrid_docs = self.hybrid_retriever.invoke(query)

        for doc in hybrid_docs:
            chunk_id = doc.metadata.get("chunk_id")
            if chunk_id in bm25_ids and chunk_id in vector_ids:
                doc.metadata["retrieval_source"] = "Hybrid (BM25 + Vector)"
            elif chunk_id in bm25_ids:
                doc.metadata["retrieval_source"] = "BM25 (Keyword)"
            elif chunk_id in vector_ids:
                doc.metadata["retrieval_source"] = "Vector (Semantic)"
            else:
                doc.metadata["retrieval_source"] = "Hybrid (Ensemble)"

        return hybrid_docs

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