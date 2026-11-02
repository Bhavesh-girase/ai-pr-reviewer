-- Historical review results do not need source snapshots to display findings.
-- Clear raw code and retrieved repository context while retaining the same JSON
-- fields for API and client compatibility.
UPDATE public.reviews AS review_row
SET review_result = jsonb_set(
    review_row.review_result,
    '{reviews}',
    COALESCE(
        (
            SELECT jsonb_agg(
                jsonb_set(
                    jsonb_set(
                        jsonb_set(
                            jsonb_set(file_review.value, '{patch}', '""'::jsonb, TRUE),
                            '{original_code}', '""'::jsonb, TRUE
                        ),
                        '{modified_code}', '""'::jsonb, TRUE
                    ),
                    '{retrieved_context}', '[]'::jsonb, TRUE
                )
                ORDER BY file_review.ordinality
            )
            FROM jsonb_array_elements(review_row.review_result -> 'reviews')
                WITH ORDINALITY AS file_review(value, ordinality)
        ),
        '[]'::jsonb
    ),
    TRUE
)
WHERE review_row.review_result IS NOT NULL
  AND jsonb_typeof(review_row.review_result -> 'reviews') = 'array';
