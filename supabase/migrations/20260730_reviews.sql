-- =========================================================
-- MIGRATION: Phase 6 Review Persistence & Review History
-- Database: Supabase PostgreSQL (Schema: public)
-- =========================================================

-- 1. Create reviews table
CREATE TABLE IF NOT EXISTS public.reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    pull_request_id UUID NOT NULL REFERENCES public.pull_requests(id) ON DELETE CASCADE,
    github_pr_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'QUEUED',
    summary TEXT,
    review_result JSONB,
    issues_count INTEGER DEFAULT 0,
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    files_reviewed INTEGER DEFAULT 0,
    lines_analyzed INTEGER DEFAULT 0,
    model_name TEXT DEFAULT 'Gemini 2.5 Flash',
    review_duration_ms INTEGER,
    base_commit_sha TEXT,
    head_commit_sha TEXT,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

-- 2. Performance & Query Indexes
CREATE INDEX IF NOT EXISTS idx_reviews_project_id ON public.reviews(project_id);
CREATE INDEX IF NOT EXISTS idx_reviews_pull_request_id ON public.reviews(pull_request_id);
CREATE INDEX IF NOT EXISTS idx_reviews_project_pr ON public.reviews(project_id, github_pr_number);
CREATE INDEX IF NOT EXISTS idx_reviews_status ON public.reviews(status);
CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON public.reviews(created_at DESC);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;

-- 4. Clean existing policies to ensure idempotency
DROP POLICY IF EXISTS "Users can view reviews for own projects" ON public.reviews;
DROP POLICY IF EXISTS "Users can insert reviews for own projects" ON public.reviews;
DROP POLICY IF EXISTS "Users can update reviews for own projects" ON public.reviews;
DROP POLICY IF EXISTS "Users can delete reviews for own projects" ON public.reviews;

-- 5. Create Row Level Security (RLS) Policies
CREATE POLICY "Users can view reviews for own projects"
    ON public.reviews FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = reviews.project_id
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert reviews for own projects"
    ON public.reviews FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = reviews.project_id
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update reviews for own projects"
    ON public.reviews FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = reviews.project_id
            AND p.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = reviews.project_id
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete reviews for own projects"
    ON public.reviews FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = reviews.project_id
            AND p.user_id = auth.uid()
        )
    );

-- 6. Force PostgREST Cache Reload
NOTIFY pgrst, 'reload schema';
