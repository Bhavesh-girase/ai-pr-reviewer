-- Durable review queue fields. Review rows in QUEUED status are pending jobs.
ALTER TABLE public.reviews
    ADD COLUMN IF NOT EXISTS worker_id TEXT,
    ADD COLUMN IF NOT EXISTS lease_expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_reviews_queued_jobs
    ON public.reviews (created_at, id)
    WHERE status = 'QUEUED';

-- Claims are serialized so the active-job cap is shared by every API instance.
CREATE OR REPLACE FUNCTION public.claim_next_review_job(
    p_worker_id TEXT,
    p_max_concurrency INTEGER,
    p_lease_seconds INTEGER,
    p_max_attempts INTEGER
)
RETURNS SETOF public.reviews
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_now TIMESTAMPTZ := clock_timestamp();
    v_running_count INTEGER;
BEGIN
    IF COALESCE(auth.role(), '') <> 'service_role' THEN
        RAISE EXCEPTION 'Service role required' USING ERRCODE = '42501';
    END IF;

    IF p_worker_id IS NULL OR p_worker_id = ''
       OR p_max_concurrency < 1 OR p_lease_seconds < 30 OR p_max_attempts < 1 THEN
        RAISE EXCEPTION 'Invalid review worker configuration' USING ERRCODE = '22023';
    END IF;

    PERFORM pg_advisory_xact_lock(hashtextextended('review_queue_global_claim', 0));

    -- Requeue abandoned work; stop retrying after the configured attempt limit.
    UPDATE public.reviews
    SET status = CASE WHEN attempt_count >= p_max_attempts THEN 'FAILED' ELSE 'QUEUED' END,
        error_message = CASE
            WHEN attempt_count >= p_max_attempts THEN 'Review worker stopped unexpectedly; retry limit reached.'
            ELSE 'Review worker stopped unexpectedly; job requeued.'
        END,
        completed_at = CASE WHEN attempt_count >= p_max_attempts THEN v_now ELSE NULL END,
        worker_id = NULL,
        lease_expires_at = NULL
    WHERE status = 'RUNNING'
      AND (
          lease_expires_at <= v_now
          OR (lease_expires_at IS NULL AND created_at < v_now - INTERVAL '15 minutes')
      );

    SELECT COUNT(*)::INTEGER
    INTO v_running_count
    FROM public.reviews
    WHERE status = 'RUNNING'
      AND lease_expires_at > v_now;

    IF v_running_count >= p_max_concurrency THEN
        RETURN;
    END IF;

    RETURN QUERY
    WITH next_job AS (
        SELECT id
        FROM public.reviews
        WHERE status = 'QUEUED'
        ORDER BY created_at, id
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    UPDATE public.reviews AS review_row
    SET status = 'RUNNING',
        attempt_count = review_row.attempt_count + 1,
        worker_id = p_worker_id,
        lease_expires_at = v_now + make_interval(secs => p_lease_seconds),
        completed_at = NULL,
        error_message = NULL
    FROM next_job
    WHERE review_row.id = next_job.id
    RETURNING review_row.*;
END;
$$;

CREATE OR REPLACE FUNCTION public.heartbeat_review_job(
    p_review_id UUID,
    p_worker_id TEXT,
    p_lease_seconds INTEGER
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
BEGIN
    IF COALESCE(auth.role(), '') <> 'service_role' THEN
        RAISE EXCEPTION 'Service role required' USING ERRCODE = '42501';
    END IF;

    UPDATE public.reviews
    SET lease_expires_at = clock_timestamp() + make_interval(secs => p_lease_seconds)
    WHERE id = p_review_id
      AND status = 'RUNNING'
      AND worker_id = p_worker_id;

    RETURN FOUND;
END;
$$;

-- A shared sliding-window limit for actual model calls, independent of user count.
CREATE TABLE IF NOT EXISTS public.ai_request_rate_limits (
    bucket TEXT PRIMARY KEY,
    request_timestamps TIMESTAMPTZ[] NOT NULL DEFAULT ARRAY[]::TIMESTAMPTZ[],
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE public.ai_request_rate_limits ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.ai_request_rate_limits FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE FUNCTION public.consume_ai_request_rate_limit(
    p_max_requests INTEGER,
    p_window_seconds INTEGER
)
RETURNS TABLE(allowed BOOLEAN, retry_after INTEGER)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_now TIMESTAMPTZ := clock_timestamp();
    v_timestamps TIMESTAMPTZ[];
    v_oldest TIMESTAMPTZ;
BEGIN
    IF COALESCE(auth.role(), '') <> 'service_role' THEN
        RAISE EXCEPTION 'Service role required' USING ERRCODE = '42501';
    END IF;
    IF p_max_requests < 1 OR p_window_seconds < 1 THEN
        RAISE EXCEPTION 'Invalid AI rate-limit configuration' USING ERRCODE = '22023';
    END IF;

    INSERT INTO public.ai_request_rate_limits (bucket)
    VALUES ('shared-llm')
    ON CONFLICT (bucket) DO NOTHING;

    SELECT limits.request_timestamps
    INTO v_timestamps
    FROM public.ai_request_rate_limits AS limits
    WHERE limits.bucket = 'shared-llm'
    FOR UPDATE;

    SELECT COALESCE(
        array_agg(active.requested_at ORDER BY active.requested_at),
        ARRAY[]::TIMESTAMPTZ[]
    )
    INTO v_timestamps
    FROM unnest(v_timestamps) AS active(requested_at)
    WHERE active.requested_at > v_now - make_interval(secs => p_window_seconds);

    IF cardinality(v_timestamps) >= p_max_requests THEN
        v_oldest := v_timestamps[1];
        UPDATE public.ai_request_rate_limits
        SET request_timestamps = v_timestamps, updated_at = v_now
        WHERE bucket = 'shared-llm';
        RETURN QUERY SELECT FALSE, GREATEST(
            1,
            CEIL(EXTRACT(EPOCH FROM (
                v_oldest + make_interval(secs => p_window_seconds) - v_now
            )))::INTEGER
        );
        RETURN;
    END IF;

    v_timestamps := array_append(v_timestamps, v_now);
    UPDATE public.ai_request_rate_limits
    SET request_timestamps = v_timestamps, updated_at = v_now
    WHERE bucket = 'shared-llm';

    RETURN QUERY SELECT TRUE, 0;
END;
$$;

REVOKE ALL ON FUNCTION public.claim_next_review_job(TEXT, INTEGER, INTEGER, INTEGER)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.claim_next_review_job(TEXT, INTEGER, INTEGER, INTEGER)
    TO service_role;
REVOKE ALL ON FUNCTION public.heartbeat_review_job(UUID, TEXT, INTEGER)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.heartbeat_review_job(UUID, TEXT, INTEGER)
    TO service_role;
REVOKE ALL ON FUNCTION public.consume_ai_request_rate_limit(INTEGER, INTEGER)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.consume_ai_request_rate_limit(INTEGER, INTEGER)
    TO service_role;

NOTIFY pgrst, 'reload schema';
