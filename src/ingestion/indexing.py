from langchain_chroma import Chroma

from src.config import embedding_function

from src.github.repository_loader import load_repository

from src.ingestion.code_chunker  import chunk_documents

from src.ingestion.data_utils import save_chunks
from pathlib import Path
from src.ingestion.data_utils  import get_chroma_directory

def build_repository_index(
    repository_path: str,
    persist_directory: str | Path | None = None,
    repository_name: str | None = None,
):
    """ Build a chroma index for an entire repository"""
    repo_name = repository_name or Path(repository_path).name
    

    documents=load_repository(repository_path)

    print(f"Documents:{len(documents)}")

    chunks=chunk_documents(documents,repository_name=repo_name)

    print(f"Chunks:{len(chunks)}")


    # Keep the legacy pickle cache for notebook/standalone callers. Project
    # indexes read their BM25 corpus from their own Chroma collection instead.
    if persist_directory is None:
        save_chunks(chunks, repo_name)

    # extracting the chunk ids 
    chunk_ids=[chunk.metadata["chunk_id"] for chunk in chunks if "chunk_id" in chunk.metadata]

    print(f"Chunk IDs:{len(chunk_ids)}")

    if chunks:
        print(chunks[0].metadata)
    

    vectorstore=Chroma(
        embedding_function=embedding_function,
        persist_directory=str(persist_directory or get_chroma_directory(repo_name)),
    )
    if chunks:
        vectorstore.add_documents(documents=chunks, ids=chunk_ids)

    return vectorstore

 
