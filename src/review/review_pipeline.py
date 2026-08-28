from src.review.prompts import REVIEW_PROMPT, format_context
from src.review.schemas import ReviewResult
from src.retrieval.retrieval_pipeline import RetrievalPipeline
from src.config import llm

MAX_DIFF_LINES_PER_FILE = 500
MAX_DIFF_CHARS_PER_FILE = 15000
TRUNCATION_MARKER = "\n[Diff truncated for review: additional lines omitted]"

def format_lines_with_limit(
    lines: list[dict],
    max_lines: int = MAX_DIFF_LINES_PER_FILE,
    max_chars: int = MAX_DIFF_CHARS_PER_FILE
) -> str:
    """
    Formats line list as 'line_no: text' strings up to max_lines and max_chars limit.
    Appends a truncation marker if the threshold is exceeded.
    Does NOT affect the full original diff retained for UI/database storage.
    """
    if not lines:
        return "(none)"

    formatted_lines: list[str] = []
    total_chars = 0
    truncated = False

    for idx, line in enumerate(lines):
        if idx >= max_lines:
            truncated = True
            break
        line_str = f"{line.get('line', idx+1)}: {line.get('text', '')}"
        if total_chars + len(line_str) + 1 > max_chars:
            truncated = True
            break
        formatted_lines.append(line_str)
        total_chars += len(line_str) + 1

    result = "\n".join(formatted_lines)
    if truncated:
        result += TRUNCATION_MARKER

    return result

class ReviewPipeline:

    def __init__(self, repository_name: str):
        self.retriever = RetrievalPipeline(repository_name)
        self.llm = llm
        self.structured_llm = llm.with_structured_output(ReviewResult)
        self.chain = REVIEW_PROMPT | self.structured_llm

    def review_file(self, file_change: dict):
        context_documents = (
            self.retriever.retrieve_context(
                file_change
            )
        )
        
        context = format_context(
            context_documents
        )
        
        added_code_str = format_lines_with_limit(file_change.get("added_lines", []))
        removed_code_str = format_lines_with_limit(file_change.get("removed_lines", []))

        review = self.chain.invoke(
            {
                "context": context,
                "filename": file_change["filename"],
                "added_code": added_code_str,
                "removed_code": removed_code_str,
            }
        )
        
        return review, context_documents

    def review_pull_request(self,changed_files):

        reviews=[]
        total_chunks=0
        for file_change in changed_files:
            review, context_documents = self.review_file(file_change)
            total_chunks += len(context_documents)

            reviews.append(
                {
                    "filename":file_change["filename"],
                    "patch":file_change.get("patch", ""),
                    "original_code": file_change.get("original_code", ""),
                    "modified_code": file_change.get("modified_code", ""),
                    "review":review,
                    "retrieved_context": [
                        {
                            "page_content": doc.page_content,
                            "metadata": doc.metadata,
                            "rerank_score": doc.metadata.get("rerank_score", 0.0),
                            "retrieval_source": doc.metadata.get("retrieval_source", "Hybrid")
                        }
                        for doc in context_documents
                    ]
                }
            )
        return reviews, total_chunks
        