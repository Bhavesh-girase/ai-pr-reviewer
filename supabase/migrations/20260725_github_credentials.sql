-- =========================================================
-- MIGRATION: GitHub Credentials Table & Security Setup
-- Database: Supabase PostgreSQL (Schema: public)
-- Target Table: github_credentials
-- =========================================================

-- 1. Create Table in public schema
CREATE TABLE IF NOT EXISTS public.github_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    github_username TEXT NOT NULL,
    github_user_id BIGINT,
    github_avatar_url TEXT,
    encrypted_pat TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Performance & Lookup Indexes
CREATE INDEX IF NOT EXISTS idx_github_credentials_user_id ON public.github_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_github_credentials_username ON public.github_credentials(github_username);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.github_credentials ENABLE ROW LEVEL SECURITY;

-- 4. Clean existing policies to ensure idempotency
DROP POLICY IF EXISTS "Users can view own github credentials" ON public.github_credentials;
DROP POLICY IF EXISTS "Users can insert own github credentials" ON public.github_credentials;
DROP POLICY IF EXISTS "Users can update own github credentials" ON public.github_credentials;
DROP POLICY IF EXISTS "Users can delete own github credentials" ON public.github_credentials;

-- 5. Create Row Level Security (RLS) Policies
CREATE POLICY "Users can view own github credentials" 
    ON public.github_credentials FOR SELECT 
    TO authenticated 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own github credentials" 
    ON public.github_credentials FOR INSERT 
    TO authenticated 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own github credentials" 
    ON public.github_credentials FOR UPDATE 
    TO authenticated 
    USING (auth.uid() = user_id) 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own github credentials" 
    ON public.github_credentials FOR DELETE 
    TO authenticated 
    USING (auth.uid() = user_id);

-- 6. Trigger for updated_at Auto-Timestamping
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_github_credentials_updated_at ON public.github_credentials;
CREATE TRIGGER update_github_credentials_updated_at
    BEFORE UPDATE ON public.github_credentials
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- 7. Force PostgREST Schema Cache Reload
NOTIFY pgrst, 'reload schema';
