from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

def format_context(documents: list[Document]) -> str:
    """
    Convert retrieved documents into a formatted context string.
    """

    context = ""

    for idx, doc in enumerate(documents, start=1):

        context += (
            f"\n{'=' * 70}\n"
            f"Chunk {idx}\n"
            f"Repository: {doc.metadata.get('repository', 'Unknown')}\n"
            f"File: {doc.metadata.get('relative_path', 'Unknown')}\n"
            f"{'=' * 70}\n"
            f"{doc.page_content}\n"
        )

    return context



REVIEW_PROMPT = ChatPromptTemplate.from_template(
    """
You are a Senior Software Engineer performing a professional GitHub Pull Request review.

Review ONLY the changed code.

Use the repository context only when it helps understand the implementation.

Repository Context
------------------
{context}

File
----
{filename}

Added Code
----------
{added_code}

Removed Code
------------
{removed_code}

Your objectives are:

- Detect bugs.
- Detect security issues.
- Detect performance problems.
- Detect maintainability issues.
- Detect code quality problems.
- Detect missing edge case handling.
- Suggest improvements only when necessary.

If the implementation looks correct, explicitly state that no significant issues were found.

For every issue you identify, you MUST extract the exact line number from the line prefixes (e.g., `12:` -> line `12`) in the "Added Code" or "Removed Code" sections, and assign it to the `line` field in your structured output. Do not hallucinate or guess any other line number.

For every issue provide:

Severity:
Explanation:
Suggestion:

Do not invent issues.

Only review what is supported by the provided context.
"""
)
    