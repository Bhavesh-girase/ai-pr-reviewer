from pathlib import Path
from langchain_core.documents import Document

# Ignore directioreies ->files and folders

IGNORE_DIRS={
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
}

SUPPORTED_EXTENSIONS={
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".jsx",
    ".tsx",
    ".cpp",
    ".js",
}

def is_supported_file(file_path: Path)->bool:
    """
    Return 1 if the file extension is supported
    """
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def should_ignore_directory(file_path: Path)->bool:
    return any(
        part in IGNORE_DIRS for part in file_path.parts
    )

def read_file(file_path: Path)->str:
    """ Read the contents of a file
    return an empty string if the file cannot be read
    """
    try:
        return file_path.read_text(
            encoding='utf-8',
            errors="ignore"
        )
    except Exception as e:
        print(f"could not read {file_path}:{e}")
        return ""

# language map for further context  generation


LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "React JSX",
    ".tsx": "React TSX",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".md": "Markdown",
    ".txt": "Text",
}


def get_language(file_path: Path)->str:
    """ return the programming language name based on the file extension"""
    return LANGUAGE_MAP.get(
        file_path.suffix.lower(),"UNKNOWN"
    )

def load_file(
    file_path: Path,
    repository_root: Path,
    repository_name: str,
) -> Document | None:
    """
    Load a single source code file into a LangChain Document.
    """

    text = read_file(file_path)

    if not text.strip():
        return None

    relative_path = file_path.relative_to(repository_root)

    return Document(
        page_content=text,
        metadata={
            "source": str(file_path),
            "file_name": file_path.name,
            "extension": file_path.suffix,
            "language": get_language(file_path),
            "relative_path": relative_path.as_posix(),
            "repository": repository_name,
        },
    )

def load_repository(repo_path: str) -> list[Document]:

    repo_path = Path(repo_path)

    repository_root = repo_path

    repository_name = repo_path.name

    documents = []

    for file_path in repo_path.rglob("*"):

        if file_path.is_dir():
            continue

        if should_ignore_directory(file_path):
            continue

        if not is_supported_file(file_path):
            continue

        document = load_file(
            file_path=file_path,
            repository_root=repository_root,
            repository_name=repository_name,
        )

        if document is not None:
            documents.append(document)

    return documents
