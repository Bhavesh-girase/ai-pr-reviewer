-- =========================================================
-- MIGRATION: Phase 4 Webhooks, Deliveries & Pull Requests
-- Database: Supabase PostgreSQL (Schema: public)
-- =========================================================

-- 1. Extend public.projects with Webhook Tracking Columns
ALTER TABLE public.projects 
ADD COLUMN IF NOT EXISTS github_webhook_id BIGINT,
ADD COLUMN IF NOT EXISTS webhook_status TEXT NOT NULL DEFAULT 'NOT_REGISTERED',
ADD COLUMN IF NOT EXISTS webhook_registered_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS webhook_secret_encrypted TEXT,
ADD COLUMN IF NOT EXISTS last_webhook_event_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_projects_webhook_status ON public.projects(webhook_status);
CREATE INDEX IF NOT EXISTS idx_projects_github_repo ON public.projects(github_owner, github_repository);

-- 2. Create Webhook Deliveries Table (Replay Protection & Audit Log)
CREATE TABLE IF NOT EXISTS public.webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    delivery_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    action TEXT,
    received_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'RECEIVED',
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_delivery_id ON public.webhook_deliveries(delivery_id);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_project_id ON public.webhook_deliveries(project_id);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_status ON public.webhook_deliveries(status);

-- 3. Create Pull Requests Table (PostgreSQL Local Cache & Persistence)
CREATE TABLE IF NOT EXISTS public.pull_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    github_pr_number INTEGER NOT NULL,
    github_pr_id BIGINT,
    title TEXT NOT NULL,
    description TEXT,
    state TEXT NOT NULL DEFAULT 'OPEN',
    draft BOOLEAN DEFAULT FALSE,
    merged BOOLEAN DEFAULT FALSE,
    author_login TEXT,
    author_avatar_url TEXT,
    source_branch TEXT,
    target_branch TEXT,
    head_sha TEXT,
    base_sha TEXT,
    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    changed_files INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    commits_count INTEGER DEFAULT 0,
    github_url TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ DEFAULT NOW(),
    last_reviewed_at TIMESTAMPTZ,
    created_from_webhook BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_project_pr_number UNIQUE (project_id, github_pr_number)
);

CREATE INDEX IF NOT EXISTS idx_pull_requests_project_id ON public.pull_requests(project_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_state ON public.pull_requests(state);
CREATE INDEX IF NOT EXISTS idx_pull_requests_updated_at ON public.pull_requests(updated_at DESC);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.webhook_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pull_requests ENABLE ROW LEVEL SECURITY;

-- 5. Clean existing policies
DROP POLICY IF EXISTS "Users can view own project webhook deliveries" ON public.webhook_deliveries;
DROP POLICY IF EXISTS "Users can view own project pull requests" ON public.pull_requests;
DROP POLICY IF EXISTS "Users can insert own project pull requests" ON public.pull_requests;
DROP POLICY IF EXISTS "Users can update own project pull requests" ON public.pull_requests;
DROP POLICY IF EXISTS "Users can delete own project pull requests" ON public.pull_requests;

-- 6. Create Row Level Security (RLS) Policies
CREATE POLICY "Users can view own project webhook deliveries"
    ON public.webhook_deliveries FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = webhook_deliveries.project_id
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view own project pull requests"
    ON public.pull_requests FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = pull_requests.project_id
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own project pull requests"
    ON public.pull_requests FOR INSERT
    TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = pull_requests.project_id
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own project pull requests"
    ON public.pull_requests FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = pull_requests.project_id
            AND p.user_id = auth.uid()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = pull_requests.project_id
            AND p.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own project pull requests"
    ON public.pull_requests FOR DELETE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = pull_requests.project_id
            AND p.user_id = auth.uid()
        )
    );

-- 7. Force PostgREST Cache Reload
NOTIFY pgrst, 'reload schema';
