-- =========================================================
-- MIGRATION: Phase 5 Automatic Repository Synchronization
-- Database: Supabase PostgreSQL (Schema: public)
-- =========================================================

-- 1. Extend public.projects with Repository Synchronization Columns
ALTER TABLE public.projects 
ADD COLUMN IF NOT EXISTS sync_status TEXT NOT NULL DEFAULT 'READY',
ADD COLUMN IF NOT EXISTS sync_error_message TEXT,
ADD COLUMN IF NOT EXISTS last_sync_started_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS last_sync_completed_at TIMESTAMPTZ;

-- 2. Add Index for sync_status query performance
CREATE INDEX IF NOT EXISTS idx_projects_sync_status ON public.projects(sync_status);

-- 3. Force PostgREST Cache Reload
NOTIFY pgrst, 'reload schema';
