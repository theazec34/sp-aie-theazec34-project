-- Brasaland Digital — job_runs (nightly orchestration layer)
-- Separate from reporting.pipeline_run_log (internal ETL audit).
-- Run in Supabase SQL Editor after telemetry_events exists.

CREATE TABLE IF NOT EXISTS job_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_name        TEXT        NOT NULL,
    target_date     DATE        NOT NULL,
    status          TEXT        NOT NULL
                    CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE job_runs IS
  'Nightly orchestration runs: CSV export + pipeline subprocess trigger. Distinct from pipeline_run_log.';

CREATE INDEX IF NOT EXISTS ix_job_runs_job_name_target_date
    ON job_runs (job_name, target_date);
