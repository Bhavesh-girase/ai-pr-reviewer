"""Persistent repository chunk storage and retrieval backed by Pinecone."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import threading
import time
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

INDEX_NAME = "repo-chunks"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
UPSERT_BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 0.5
EMBEDDING_MODEL = "models/text-embedding-004"

_TRANSIENT_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}
_client: Any | None = None
_index: Any | None = None
_client_api_key: str | None = None
_index_dimension: int | None = None
_client_lock = threading.Lock()
_embedding_model: Any | None = None
_embedding_lock = threading.Lock()


class PineconeStorageError(RuntimeError):
    """Raised when a Pinecone operation fails or its response is invalid."""


class PineconeConfigurationError(PineconeStorageError):
    """Raised when Pinecone or its embedding provider is not configured."""


class EmbeddingError(RuntimeError):
    """Raised when text cannot be converted to an embedding vector."""


def _get_client_and_index() -> tuple[Any, Any]:
    """Create the official Pinecone client lazily so importing this module is safe."""
    global _client, _index, _client_api_key, _index_dimension

    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise PineconeConfigurationError(
            "PINECONE_API_KEY is not set; add it to the backend environment."
        )

    if _client is not None and _index is not None and _client_api_key == api_key:
        return _client, _index

    with _client_lock:
        if _client is not None and _index is not None and _client_api_key == api_key:
            return _client, _index

        try:
            from pinecone import Pinecone
        except ImportError as exc:
            raise PineconeConfigurationError(
                "The official 'pinecone' package is required; install the project requirements."
            ) from exc

        def connect() -> tuple[Any, Any]:
            client = Pinecone(api_key=api_key)
            return client, client.Index(INDEX_NAME)

        client, index = _run_pinecone_request(
            connect, f"connect to the configured index '{INDEX_NAME}'"
        )

        _client = client
        _index = index
        _client_api_key = api_key
        _index_dimension = None
        return client, index


def _get_embedding_model() -> Any:
    global _embedding_model

    if _embedding_model is not None:
        return _embedding_model

    with _embedding_lock:
        if _embedding_model is not None:
            return _embedding_model
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
        except ImportError as exc:
            raise PineconeConfigurationError(
                "langchain-google-genai is required for the default Gemini embeddings."
            ) from exc

        model_name = os.environ.get("GEMINI_EMBEDDING_MODEL", EMBEDDING_MODEL)
        google_api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        try:
            _embedding_model = GoogleGenerativeAIEmbeddings(
                model=model_name,
                google_api_key=google_api_key,
            )
        except Exception as exc:
            raise PineconeConfigurationError(
                "Could not initialize Gemini embeddings; configure GEMINI_API_KEY."
            ) from exc
        return _embedding_model


def _get_index_dimension(client: Any) -> int:
    global _index_dimension

    if _index_dimension is not None:
        return _index_dimension

    description = _run_pinecone_request(
        lambda: client.describe_index(INDEX_NAME), "read the index dimensions"
    )
    dimension = _response_field(description, "dimension")
    try:
        dimension = int(dimension)
    except (TypeError, ValueError) as exc:
        raise PineconeStorageError(
            f"Pinecone index '{INDEX_NAME}' did not report a valid vector dimension."
        ) from exc
    if dimension < 1:
        raise PineconeStorageError(
            f"Pinecone index '{INDEX_NAME}' reported an invalid vector dimension."
        )

    _index_dimension = dimension
    return dimension


def _response_field(response: Any, name: str, default: Any = None) -> Any:
    if isinstance(response, Mapping):
        return response.get(name, default)
    return getattr(response, name, default)


def _error_status_code(exc: Exception) -> int | None:
    response = getattr(exc, "response", None)
    candidates = (
        getattr(exc, "status", None),
        getattr(exc, "status_code", None),
        getattr(response, "status_code", None),
    )
    for candidate in candidates:
        try:
            if candidate is not None:
                return int(candidate)
        except (TypeError, ValueError):
            continue
    return None


def _is_transient_error(exc: Exception) -> bool:
    current: Any = exc
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        status_code = _error_status_code(current)
        if status_code in _TRANSIENT_STATUS_CODES:
            return True

        # Pinecone SDK and HTTP transports have used different exception
        # classes across versions; inspect chained causes without pinning internals.
        class_name = type(current).__name__.lower()
        if any(
            marker in class_name
            for marker in (
                "timeout",
                "connection",
                "connecterror",
                "networkerror",
                "maxretry",
                "protocolerror",
                "temporarilyunavailable",
                "serviceunavailable",
                "ratelimit",
                "toomanyrequests",
            )
        ) or isinstance(current, (TimeoutError, ConnectionError)):
            return True

        current = (
            getattr(current, "__cause__", None)
            or getattr(current, "__context__", None)
            or getattr(current, "reason", None)
        )
    return False


def _run_pinecone_request(operation: Any, description: str) -> Any:
    for attempt in range(MAX_RETRIES):
        try:
            return operation()
        except Exception as exc:
            if not _is_transient_error(exc):
                raise PineconeStorageError(
                    f"Pinecone failed to {description}."
                ) from exc

            if attempt + 1 == MAX_RETRIES:
                raise PineconeStorageError(
                    f"Pinecone timed out or rate-limited the request to {description} "
                    f"after {MAX_RETRIES} attempts."
                ) from exc

            delay = RETRY_BASE_DELAY_SECONDS * (2**attempt)
            logger.warning(
                "Transient Pinecone error while trying to %s; retrying in %.1fs "
                "(attempt %d/%d).",
                description,
                delay,
                attempt + 1,
                MAX_RETRIES,
            )
            time.sleep(delay)

    raise AssertionError("unreachable")


def _coerce_vector(values: Sequence[Any], *, context: str) -> list[float]:
    try:
        vector = [float(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise EmbeddingError(
            f"The embedding provider returned an invalid {context} vector."
        ) from exc

    if not vector or not all(math.isfinite(value) for value in vector):
        raise EmbeddingError(f"The embedding provider returned an invalid {context} vector.")
    return vector


def _embed_documents(texts: list[str], embeddings: Any | None) -> list[list[float]]:
    if not texts:
        return []
    provider = embeddings if embeddings is not None else _get_embedding_model()
    try:
        if hasattr(provider, "embed_documents"):
            raw_vectors = provider.embed_documents(texts)
        elif callable(provider):
            raw_vectors = [provider(text) for text in texts]
        else:
            raise TypeError("embeddings must provide embed_documents() or be callable")
        if len(raw_vectors) != len(texts):
            raise ValueError("embedding count did not match text count")
        return [
            _coerce_vector(vector, context="document") for vector in raw_vectors
        ]
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError("Failed to generate repository chunk embeddings.") from exc


def embed_text(text: str, *, embeddings: Any | None = None) -> list[float]:
    """Convert one query string to a dense vector using the configured embedder.

    Pass a LangChain embeddings instance (or a callable) to customize the
    provider. By default, Gemini ``text-embedding-004`` is used.
    """
    provider = embeddings if embeddings is not None else _get_embedding_model()
    try:
        if hasattr(provider, "embed_query"):
            vector = provider.embed_query(text)
        elif callable(provider):
            vector = provider(text)
        else:
            raise TypeError("embeddings must provide embed_query() or be callable")
        return _coerce_vector(vector, context="query")
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError("Failed to generate the search query embedding.") from exc


def _validate_vector_dimensions(
    vectors: Sequence[Sequence[float]], dimension: int
) -> None:
    for vector in vectors:
        if len(vector) != dimension:
            raise PineconeStorageError(
                f"Embedding dimension {len(vector)} does not match Pinecone index "
                f"dimension {dimension}. Configure an embedding model with matching dimensions."
            )


def _stable_chunk_id(repo_name: str, file_path: str, chunk_index: int) -> str:
    identity = json.dumps(
        [repo_name, file_path, chunk_index], ensure_ascii=False, separators=(",", ":")
    )
    return "chunk_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


def index_repository(
    repo_name: str,
    files_data: list[dict[str, str]],
    *,
    embeddings: Any | None = None,
) -> int:
    """Split and persist repository source files in the shared Pinecone index.

    Returns the number of chunks upserted. Each upsert request contains at most
    100 vectors, and source text is retained in Pinecone metadata.
    """
    if not isinstance(repo_name, str) or not repo_name.strip():
        raise ValueError("repo_name must be a non-empty string")
    if not isinstance(files_data, list):
        raise TypeError("files_data must be a list of {'file_path', 'content'} dictionaries")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    records: list[dict[str, Any]] = []
    for file_data in files_data:
        if not isinstance(file_data, dict):
            raise TypeError("each files_data entry must be a dictionary")
        file_path = file_data.get("file_path")
        content = file_data.get("content")
        if not isinstance(file_path, str) or not isinstance(content, str):
            raise ValueError("each file must contain string 'file_path' and 'content' fields")

        for chunk_index, text in enumerate(splitter.split_text(content)):
            records.append(
                {
                    "id": _stable_chunk_id(repo_name, file_path, chunk_index),
                    "file_path": file_path,
                    "text": text,
                }
            )

    if not records:
        return 0

    client, index = _get_client_and_index()
    dimension = _get_index_dimension(client)

    for start in range(0, len(records), UPSERT_BATCH_SIZE):
        batch_records = records[start : start + UPSERT_BATCH_SIZE]
        vectors = _embed_documents(
            [record["text"] for record in batch_records], embeddings
        )
        _validate_vector_dimensions(vectors, dimension)
        batch = [
            {
                "id": record["id"],
                "values": vector,
                "metadata": {
                    "repo": repo_name,
                    "file_path": record["file_path"],
                    "text": record["text"],
                },
            }
            for record, vector in zip(batch_records, vectors)
        ]
        _run_pinecone_request(
            lambda batch=batch: index.upsert(vectors=batch),
            "upsert repository chunks",
        )

    return len(records)


def is_repo_already_indexed(repo_name: str) -> bool:
    """Return whether Pinecone has at least one vector for this repository."""
    if not isinstance(repo_name, str) or not repo_name.strip():
        raise ValueError("repo_name must be a non-empty string")

    client, index = _get_client_and_index()
    dimension = _get_index_dimension(client)
    response = _run_pinecone_request(
        lambda: index.query(
            vector=[0.0] * dimension,
            top_k=1,
            filter={"repo": repo_name},
            include_metadata=False,
        ),
        "check whether the repository is indexed",
    )
    matches = _response_field(response, "matches", []) or []
    return bool(matches)


def search_repo_chunks(
    repo_name: str,
    query: str,
    top_k: int = 5,
    *,
    embeddings: Any | None = None,
) -> list[dict[str, Any]]:
    """Search repository-scoped chunks and return file, score, and source text."""
    if not isinstance(repo_name, str) or not repo_name.strip():
        raise ValueError("repo_name must be a non-empty string")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty string")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer")

    query_vector = embed_text(query, embeddings=embeddings)
    client, index = _get_client_and_index()
    dimension = _get_index_dimension(client)
    _validate_vector_dimensions([query_vector], dimension)

    response = _run_pinecone_request(
        lambda: index.query(
            vector=query_vector,
            top_k=top_k,
            filter={"repo": repo_name},
            include_metadata=True,
        ),
        "search repository chunks",
    )

    matches = _response_field(response, "matches", []) or []
    results: list[dict[str, Any]] = []
    for match in matches:
        metadata = _response_field(match, "metadata", {}) or {}
        results.append(
            {
                "file_path": _response_field(metadata, "file_path"),
                "score": _response_field(match, "score"),
                "text": _response_field(metadata, "text"),
            }
        )
    return results


__all__ = [
    "EmbeddingError",
    "PineconeConfigurationError",
    "PineconeStorageError",
    "embed_text",
    "index_repository",
    "is_repo_already_indexed",
    "search_repo_chunks",
]
