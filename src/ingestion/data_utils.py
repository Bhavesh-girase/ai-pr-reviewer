
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pickle
from src.config import CHUNK_SIZE,CHUNK_OVERLAP,DOCS_DIR
from pathlib import Path
from src.config import PROCESSED_DIR,CHROMA_BASE_DIR

def create_chunks():
    # 1. Define the folder path
    pdf_folder = DOCS_DIR
    docs = []
    
    # 2. Iterate through all PDFs in the folder
    for pdf in pdf_folder.glob("*.pdf"):
        loader = PyPDFLoader(str(pdf))
        docs.extend(loader.load())
    
    # 3. Split the combined documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(docs)
    
    return chunks


def get_chunk_file(repository_name: str) ->Path:
    repo_dir=PROCESSED_DIR / repository_name

    repo_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return repo_dir / "chunks.pkl"


def save_chunks(chunks,repository_name: str):

    chunk_file=get_chunk_file(repository_name)

    with open(chunk_file,"wb") as f:
        pickle.dump(chunks,f)
        
    

def load_chunks(
    repository_name: str,
):

    chunk_file = get_chunk_file(
        repository_name
    )

    with open(chunk_file, "rb") as f:

        return pickle.load(f)


def get_chroma_directory(
    repository_name: str,
) -> Path:

    chroma_dir = (
        CHROMA_BASE_DIR
        / repository_name
    )

    chroma_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return chroma_dir

    
