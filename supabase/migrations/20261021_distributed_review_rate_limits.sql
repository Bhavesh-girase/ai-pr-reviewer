-- Shared, per-user sliding-window review limits across backend workers.
CREATE TABLE IF NOT EXISTS public.review_rate_limits (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    request_timestamps TIMESTAMPTZ[] NOT NULL DEFAULT ARRAY[]::TIMESTAMPTZ[],
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.review_rate_limits ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.review_rate_limits FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE FUNCTION public.consume_review_rate_limit(
    p_max_requests INTEGER,
    p_window_seconds INTEGER
)
RETURNS TABLE(allowed BOOLEAN, retry_after INTEGER)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    v_user_id UUID := auth.uid();
    v_now TIMESTAMPTZ := clock_timestamp();
    v_timestamps TIMESTAMPTZ[];
    v_oldest TIMESTAMPTZ;
    v_retry_after INTEGER;
BEGIN
    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Authentication required' USING ERRCODE = '28000';
    END IF;

    IF p_max_requests < 1 OR p_window_seconds < 1 THEN
        RAISE EXCEPTION 'Invalid review rate-limit configuration' USING ERRCODE = '22023';
    END IF;

    -- The unique user row serializes concurrent claims for this identity.
    INSERT INTO public.review_rate_limits (user_id)
    VALUES (v_user_id)
    ON CONFLICT (user_id) DO NOTHING;

    SELECT limits.request_timestamps
    INTO v_timestamps
    FROM public.review_rate_limits AS limits
    WHERE limits.user_id = v_user_id
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
        v_retry_after := GREATEST(
            1,
            CEIL(EXTRACT(EPOCH FROM (
                v_oldest + make_interval(secs => p_window_seconds) - v_now
            )))::INTEGER
        );

        UPDATE public.review_rate_limits
        SET request_timestamps = v_timestamps,
            updated_at = v_now
        WHERE user_id = v_user_id;

        RETURN QUERY SELECT FALSE, v_retry_after;
        RETURN;
    END IF;

    v_timestamps := array_append(v_timestamps, v_now);
    UPDATE public.review_rate_limits
    SET request_timestamps = v_timestamps,
        updated_at = v_now
    WHERE user_id = v_user_id;

    RETURN QUERY SELECT TRUE, 0;
END;
$$;

REVOKE ALL ON FUNCTION public.consume_review_rate_limit(INTEGER, INTEGER) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.consume_review_rate_limit(INTEGER, INTEGER) TO authenticated;

NOTIFY pgrst, 'reload schema';
