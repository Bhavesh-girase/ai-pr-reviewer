from src.ingestion import pinecone_store


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [[float(len(text)), 1.0, 2.0] for text in texts]

    def embed_query(self, text):
        return [float(len(text)), 1.0, 2.0]


class FakeClient:
    def describe_index(self, name):
        assert name == "repo-chunks"
        return {"dimension": 3}


class FakeIndex:
    def __init__(self):
        self.upsert_batches = []
        self.query_arguments = []

    def upsert(self, *, vectors):
        self.upsert_batches.append(vectors)

    def query(self, **kwargs):
        self.query_arguments.append(kwargs)
        if kwargs["include_metadata"]:
            return {
                "matches": [
                    {
                        "metadata": {
                            "file_path": "src/app.py",
                            "text": "def run(): pass",
                        },
                        "score": 0.92,
                    }
                ]
            }
        return {"matches": [{"id": "chunk-1"}]}


def _use_fake_index(monkeypatch, index):
    client = FakeClient()
    monkeypatch.setattr(
        pinecone_store, "_get_client_and_index", lambda: (client, index)
    )
    monkeypatch.setattr(pinecone_store, "_index_dimension", None)


def test_index_repository_batches_and_keeps_chunk_metadata(monkeypatch):
    index = FakeIndex()
    _use_fake_index(monkeypatch, index)
    files = [
        {"file_path": f"src/file_{number}.py", "content": f"value = {number}"}
        for number in range(105)
    ]

    indexed_count = pinecone_store.index_repository(
        "facebook/react", files, embeddings=FakeEmbeddings()
    )

    assert indexed_count == 105
    assert [len(batch) for batch in index.upsert_batches] == [100, 5]
    first_vector = index.upsert_batches[0][0]
    assert first_vector["metadata"] == {
        "repo": "facebook/react",
        "file_path": "src/file_0.py",
        "text": "value = 0",
    }
    assert first_vector["id"].startswith("chunk_")
    assert len(first_vector["id"]) == len("chunk_") + 64
    assert index.upsert_batches[0][0]["id"] != index.upsert_batches[0][1]["id"]


def test_repo_exists_uses_repo_filter_and_returns_match(monkeypatch):
    index = FakeIndex()
    _use_fake_index(monkeypatch, index)

    assert pinecone_store.is_repo_already_indexed("facebook/react") is True
    assert index.query_arguments[0]["vector"] == [0.0, 0.0, 0.0]
    assert index.query_arguments[0]["filter"] == {"repo": "facebook/react"}
    assert index.query_arguments[0]["top_k"] == 1


def test_search_returns_clean_results_and_uses_repository_filter(monkeypatch):
    index = FakeIndex()
    _use_fake_index(monkeypatch, index)

    results = pinecone_store.search_repo_chunks(
        "facebook/react", "where is run defined?", embeddings=FakeEmbeddings()
    )

    assert results == [
        {
            "file_path": "src/app.py",
            "score": 0.92,
            "text": "def run(): pass",
        }
    ]
    assert index.query_arguments[0]["filter"] == {"repo": "facebook/react"}
    assert index.query_arguments[0]["include_metadata"] is True


def test_index_repository_rejects_embedding_dimension_mismatch(monkeypatch):
    index = FakeIndex()
    _use_fake_index(monkeypatch, index)

    class WrongDimensionEmbeddings:
        def embed_documents(self, texts):
            return [[1.0, 2.0] for _ in texts]

    try:
        pinecone_store.index_repository(
            "facebook/react",
            [{"file_path": "src/app.py", "content": "print('hi')"}],
            embeddings=WrongDimensionEmbeddings(),
        )
    except pinecone_store.PineconeStorageError as exc:
        assert "does not match Pinecone index dimension" in str(exc)
    else:
        raise AssertionError("expected a vector dimension validation error")
