from pathlib import Path
from src.ingestion.indexing import build_repository_index
from src.ingestion.data_utils import get_chroma_directory
from src.ingestion.repository_registry import RepositoryRegistry

class IndexManager:
    def __init__(self):
        self.registry=RepositoryRegistry()

    def index_exists(self, repository_name: str, persist_directory=None) -> bool:
        chroma_dir = (
            get_chroma_directory(repository_name)
            if persist_directory is None
            else Path(persist_directory)
        )
        return chroma_dir.exists() and any(chroma_dir.iterdir())

    def ensure_index(self, repository_path: str, persist_directory=None, repository_name=None):
        repository_name = repository_name or Path(repository_path).name

        # Project indexes have an explicit, isolated location managed by
        # ProjectProvisioner and IncrementalIndexer. Do not use the global
        # repository registry to decide whether that separate index exists.
        if persist_directory is not None:
            if self.index_exists(repository_name, persist_directory):
                return
            build_repository_index(
                repository_path,
                persist_directory=persist_directory,
                repository_name=repository_name,
            )
            return

        if (
            self.registry.is_registered(repository_name)
            and self.index_exists(repository_name)
        ):
            return
        
        print(f"Building index for '{repository_name}'")

        build_repository_index(repository_path, repository_name=repository_name)
        self.registry.register(repository_name)
