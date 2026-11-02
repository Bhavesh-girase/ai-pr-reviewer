from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from src.ingestion.index_manager import IndexManager
from src.retrieval.retrieval_pipeline import RetrievalPipeline
from src.pr_reviewer import PRReviewer


def test_project_retrieval_builds_bm25_from_the_project_chroma_snapshot(tmp_path):
    vectorstore = MagicMock()
    vectorstore.get.return_value = {
        "documents": ["latest indexed code"],
        "metadatas": [{"relative_path": "src/app.py"}],
    }
    bm25 = object()

    with patch(
        "src.retrieval.retrieval_pipeline.load_vectorstore",
        return_value=vectorstore,
    ), patch(
        "src.retrieval.retrieval_pipeline.create_bm25",
        return_value=bm25,
    ) as create_bm25, patch(
        "src.retrieval.retrieval_pipeline.create_hybrid_retriever",
        return_value=MagicMock(),
    ), patch("src.retrieval.retrieval_pipeline.load_reranker", return_value=MagicMock()):
        pipeline = RetrievalPipeline("project-id", persist_directory=tmp_path)

    assert pipeline.chunks == [
        Document(
            page_content="latest indexed code",
            metadata={"relative_path": "src/app.py"},
        )
    ]
    create_bm25.assert_called_once_with(pipeline.chunks)


def test_index_manager_reuses_and_builds_only_the_explicit_project_index(tmp_path):
    repository_path = tmp_path / "repository"
    repository_path.mkdir()
    project_index = tmp_path / "project-index"
    project_index.mkdir()

    manager = IndexManager.__new__(IndexManager)
    manager.registry = MagicMock()

    with patch("src.ingestion.index_manager.build_repository_index") as build_index:
        manager.ensure_index(
            str(repository_path),
            persist_directory=project_index,
            repository_name="github-repo",
        )
        build_index.assert_called_once_with(
            str(repository_path),
            persist_directory=project_index,
            repository_name="github-repo",
        )

        # A subsequent call sees the same persisted project index and does not
        # rebuild it or consult the unrelated global registry.
        (project_index / "chroma.sqlite3").touch()
        manager.ensure_index(
            str(repository_path),
            persist_directory=project_index,
            repository_name="github-repo",
        )

    build_index.assert_called_once()
    manager.registry.is_registered.assert_not_called()


def test_project_review_reuses_synced_checkout_and_index(tmp_path):
    repository_path = tmp_path / "project-id"
    (repository_path / ".git").mkdir(parents=True)
    chroma_path = tmp_path / "project-index"

    reviewer = PRReviewer.__new__(PRReviewer)
    reviewer.github_token = "test-token"
    reviewer.github = MagicMock()
    reviewer.github.get_pull_request.return_value = {
        "base": {"sha": "base-sha", "ref": "main"},
        "head": {"sha": "head-sha", "ref": "feature"},
    }
    reviewer.github.get_pull_request_files.return_value = []
    reviewer.index_manager = MagicMock()

    with patch("src.pr_reviewer.prepare_repository") as prepare_repository, patch(
        "git.Repo"
    ) as git_repo, patch("src.pr_reviewer.ReviewPipeline") as review_pipeline:
        review_pipeline.return_value.review_pull_request.return_value = ([], 0)

        result = reviewer.review(
            repo_url="https://github.com/acme/service",
            owner="acme",
            repository="service",
            pull_number=7,
            local_path=repository_path,
            chroma_path=chroma_path,
        )

    prepare_repository.assert_not_called()
    reviewer.index_manager.ensure_index.assert_called_once_with(
        str(repository_path),
        persist_directory=chroma_path,
        repository_name="service",
    )
    review_pipeline.assert_called_once_with("project-id", persist_directory=chroma_path)
    git_repo.assert_called_once_with(repository_path)
    assert result["reviews"] == []
