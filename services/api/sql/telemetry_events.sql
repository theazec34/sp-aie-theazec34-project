-- Brasaland Digital — telemetry_events (Supabase / Postgres)
-- Append-only fact table. Run in Supabase SQL Editor once.
-- Invariants: write-only (no UPDATE/DELETE), fixed analytical columns + JSONB tags.

CREATE TABLE IF NOT EXISTS telemetry_events (
    id              BIGSERIAL PRIMARY KEY,
    event_id        TEXT        NOT NULL UNIQUE,
    event_type      TEXT        NOT NULL,
    "timestamp"     TIMESTAMPTZ NOT NULL,
    service         TEXT        NOT NULL,
    session_id      TEXT,
    user_id         TEXT,
    tags            JSONB       NOT NULL DEFAULT '{}'::jsonb
);

COMMENT ON TABLE telemetry_events IS
  'Append-only telemetry facts. tags holds allowlisted properties (+ schema_version, request_id).';
COMMENT ON COLUMN telemetry_events.service IS
  'Emitter service, e.g. backoffice';
COMMENT ON COLUMN telemetry_events.tags IS
  'JSONB properties allowlist from event envelope; query with GIN';

CREATE INDEX IF NOT EXISTS ix_telemetry_events_timestamp
    ON telemetry_events ("timestamp");

CREATE INDEX IF NOT EXISTS ix_telemetry_events_event_type
    ON telemetry_events (event_type);

CREATE INDEX IF NOT EXISTS ix_telemetry_events_tags_gin
    ON telemetry_events USING GIN (tags);

-- Reject mutations: telemetry is immutable once written.
CREATE OR REPLACE FUNCTION reject_telemetry_events_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'telemetry_events is append-only: % not allowed', TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS trg_telemetry_events_no_update ON telemetry_events;
CREATE TRIGGER trg_telemetry_events_no_update
    BEFORE UPDATE ON telemetry_events
    FOR EACH ROW
    EXECUTE PROCEDURE reject_telemetry_events_mutation();

DROP TRIGGER IF EXISTS trg_telemetry_events_no_delete ON telemetry_events;
CREATE TRIGGER trg_telemetry_events_no_delete
    BEFORE DELETE ON telemetry_events
    FOR EACH ROW
    EXECUTE PROCEDURE reject_telemetry_events_mutation();
