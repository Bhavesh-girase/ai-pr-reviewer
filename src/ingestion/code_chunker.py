from langchain_text_splitters import(
    RecursiveCharacterTextSplitter,
    Language
)
from langchain_core.documents import Document

LANGUAGE_SPLITTERS = {
    "Python": Language.PYTHON,
    "JavaScript": Language.JS,
    "TypeScript": Language.TS,
    "React JSX": Language.JS,       # Uses JavaScript splitter
    "React TSX": Language.TS,       # Uses TypeScript splitter
    "Java": Language.JAVA,
    "C++": Language.CPP,
    "C": Language.CPP,              # Uses C++ splitter
    "C#": Language.CSHARP,
    "Go": Language.GO,
    "Rust": Language.RUST,
    "Markdown": Language.MARKDOWN,
}
def chunk_documents(
    documents:list[Document],
    repository_name: str,
    chunk_size:int=1000,
    chunk_overlap:int=150
):
    """split repository documents into smaller chunks while preserving the metadata with chunks"""
    chunked_documents=[]

    for document in documents:
        language=document.metadata.get("language")

        if language in LANGUAGE_SPLITTERS:

            splitter=RecursiveCharacterTextSplitter.from_language(
                language=LANGUAGE_SPLITTERS[language],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        else:

            splitter=RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        chunks=splitter.split_documents([document])

        relative_path=document.metadata["relative_path"]
        for index,chunk in enumerate(chunks):
            chunk.metadata["chunk_index"]=index
            chunk.metadata["repository"]=repository_name
            chunk.metadata["chunk_id"]=(
                f"{relative_path}:{index}"
            )
            chunked_documents.append(chunk)
    return chunked_documents
        
