import logging
from pathlib import Path
from typing import Optional, List, Tuple
from langchain_chroma import Chroma

from src.config import embedding_function
from src.ingestion.code_chunker import chunk_documents
from src.ingestion.data_utils import get_chroma_directory
from src.github.repository_loader import load_file, is_supported_file, should_ignore_directory

logger = logging.getLogger(__name__)

class IncrementalIndexer:
    """
    Manages incremental ChromaDB vector store updates for a repository workspace.
    Selectively purges obsolete/deleted file chunks and embeds new/modified files.
    """

    def __init__(self, repository_name: str, persist_directory: Optional[str | Path] = None):
        self.repository_name = repository_name
        self.persist_directory = str(persist_directory) if persist_directory else str(get_chroma_directory(repository_name))

        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=embedding_function,
        )
        self.collection = self.vectorstore._collection

    def delete_file_chunks(self, relative_path: str) -> int:
        """
        Deletes all chunks associated with the relative file path from ChromaDB.
        """
        # Normalize slashes for consistency across platforms
        normalized_path = relative_path.replace("\\", "/")
        try:
            # Query existing IDs by relative_path metadata
            existing = self.collection.get(where={"relative_path": normalized_path})
            ids_to_delete = existing.get("ids", []) if existing else []
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"Purged {len(ids_to_delete)} chunks for deleted/modified file '{normalized_path}'")
                return len(ids_to_delete)
            return 0
        except Exception as e:
            logger.warning(f"Failed to delete chunks for '{normalized_path}': {str(e)}")
            return 0

    def index_single_file(self, repository_root: Path, relative_path: str) -> int:
        """
        Loads, chunks, embeds, and adds a single file to ChromaDB.
        """
        normalized_path = relative_path.replace("\\", "/")
        file_path = repository_root / relative_path

        if not file_path.exists() or file_path.is_dir():
            return 0

        if should_ignore_directory(file_path) or not is_supported_file(file_path):
            return 0

        document = load_file(
            file_path=file_path,
            repository_root=repository_root,
            repository_name=self.repository_name,
        )
        if not document:
            return 0

        # Ensure metadata has normalized relative_path
        document.metadata["relative_path"] = normalized_path

        chunks = chunk_documents([document], repository_name=self.repository_name)
        if not chunks:
            return 0

        for chunk in chunks:
            chunk.metadata["relative_path"] = normalized_path

        chunk_ids = [chunk.metadata["chunk_id"] for chunk in chunks if "chunk_id" in chunk.metadata]

        self.vectorstore.add_documents(documents=chunks, ids=chunk_ids)
        logger.info(f"Indexed {len(chunks)} chunks for file '{normalized_path}'")
        return len(chunks)

    def update_files(self, repository_path: str, changed_files: List[str]) -> int:
        """
        Legacy compatibility method: Purges and re-indexes a list of changed files.
        """
        repo_root = Path(repository_path)
        total_chunks = 0
        for rel_path in changed_files:
            self.delete_file_chunks(rel_path)
            total_chunks += self.index_single_file(repo_root, rel_path)
        return total_chunks

    def sync_changes(
        self,
        repository_path: str,
        added_files: List[str],
        modified_files: List[str],
        deleted_files: List[str],
        renamed_files: List[Tuple[str, str]],
    ) -> int:
        """
        Atomically applies structured Git changes to the ChromaDB index:
        - Deleted files: removes all chunks
        - Renamed files: removes old chunks, indexes new file
        - Modified files: removes old chunks, re-indexes new content
        - Added files: indexes new content
        """
        repo_root = Path(repository_path)
        total_indexed = 0

        # 1. Handle Deleted Files
        for del_path in deleted_files:
            self.delete_file_chunks(del_path)

        # 2. Handle Renamed Files: (old_path, new_path)
        for old_path, new_path in renamed_files:
            self.delete_file_chunks(old_path)
            total_indexed += self.index_single_file(repo_root, new_path)

        # 3. Handle Modified Files
        for mod_path in modified_files:
            self.delete_file_chunks(mod_path)
            total_indexed += self.index_single_file(repo_root, mod_path)

        # 4. Handle Added Files
        for add_path in added_files:
            self.delete_file_chunks(add_path)  # Safety purge if re-added
            total_indexed += self.index_single_file(repo_root, add_path)

        logger.info(
            f"ChromaDB incremental sync complete for '{self.repository_name}': "
            f"Added={len(added_files)}, Modified={len(modified_files)}, "
            f"Deleted={len(deleted_files)}, Renamed={len(renamed_files)}, TotalChunksAdded={total_indexed}"
        )
        return total_indexed