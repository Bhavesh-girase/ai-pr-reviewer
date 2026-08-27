-- =========================================================
-- MIGRATION: Projects Table & Provisioning Status Setup
-- Database: Supabase PostgreSQL (Schema: public)
-- Target Table: public.projects
-- =========================================================

-- 1. Create Status Enum Type (if not already existing)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'project_status') THEN
        CREATE TYPE project_status AS ENUM ('CREATING', 'CLONING', 'INDEXING', 'READY', 'FAILED');
    END IF;
END$$;

-- 2. Create Projects Table
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_name TEXT NOT NULL,
    github_owner TEXT NOT NULL,
    github_repository TEXT NOT NULL,
    default_branch TEXT NOT NULL DEFAULT 'main',
    auth_type TEXT NOT NULL DEFAULT 'connected_account',
    custom_token TEXT,
    clone_path TEXT,
    chroma_path TEXT,
    current_commit_hash TEXT,
    last_indexed_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    status project_status NOT NULL DEFAULT 'CREATING',
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Performance & Lookup Indexes
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON public.projects(created_at DESC);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

-- 5. Clean existing policies to ensure idempotency
DROP POLICY IF EXISTS "Users can view own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can insert own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can update own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can delete own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can manage own projects" ON public.projects;

-- 6. Create Row Level Security (RLS) Policies
CREATE POLICY "Users can view own projects"
    ON public.projects FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own projects"
    ON public.projects FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects"
    ON public.projects FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects"
    ON public.projects FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- 7. Trigger for updated_at Auto-Timestamping
CREATE OR REPLACE FUNCTION public.update_projects_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_projects_updated_at ON public.projects;
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW
    EXECUTE FUNCTION public.update_projects_updated_at_column();

-- 8. Force PostgREST Schema Cache Reload
NOTIFY pgrst, 'reload schema';
