from src.review.prompts import REVIEW_PROMPT,format_context
from src.review.schemas import ReviewResult
from src.retrieval.retrieval_pipeline import RetrievalPipeline
from src.config import llm

class ReviewPipeline:

    def __init__(self,repository_name: str):
        self.retriever=RetrievalPipeline(repository_name)

        self.llm=llm

        self.structured_llm=llm.with_structured_output(ReviewResult)


        self.chain=REVIEW_PROMPT | self.structured_llm

    def review_file(self,file_change: dict):
        context_documents = (
            self.retriever.retrieve_context(
                file_change
            )
        )
        
        context = format_context(
            context_documents
        )
        
        review = self.chain.invoke(
            {
                "context": context,
                "filename": file_change["filename"],
                "added_code": "\n".join(
                    f"{line['line']}: {line['text']}"
                    for line in file_change["added_lines"]
                ),
                "removed_code": "\n".join(
                    f"{line['line']}: {line['text']}"
                    for line in file_change["removed_lines"]
                ),
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
        