BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gymdb_app') THEN
        CREATE ROLE gymdb_app LOGIN PASSWORD 'gymdb_app_password';
    END IF;

    EXECUTE format(
        'GRANT CONNECT ON DATABASE %I TO gymdb_app',
        current_database()
    );
END
$$;

GRANT USAGE ON SCHEMA public TO gymdb_app;
GRANT SELECT ON TABLE public.gyms TO gymdb_app;

GRANT USAGE ON SCHEMA ops TO gymdb_app;
GRANT SELECT, INSERT, UPDATE ON TABLE ops.job_receipts TO gymdb_app;

COMMIT;
