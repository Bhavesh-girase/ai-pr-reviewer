from pathlib import Path
from src.ingestion.indexing import build_repository_index
from src.ingestion.data_utils import get_chroma_directory
from src.ingestion.repository_registry import RepositoryRegistry

class IndexManager:
    def __init__(self):
        self.registry=RepositoryRegistry()

    def index_exists(self,repository_name:str)->bool:
        chroma_dir=get_chroma_directory(repository_name)

        return any(chroma_dir.iterdir())

    def ensure_index(self,repository_path:str):
        repository_name=Path(repository_path).name
        if (
            self.registry.is_registered(repository_name)
            and self.index_exists(repository_name)
        ):
            return
        
        print(f"Building index for '{repository_name}'")

        build_repository_index(repository_path)
        self.registry.register(repository_name)