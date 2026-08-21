-- Brasaland Digital — reporting schema + weekly location performance
-- Destination for the business performance pipeline (never telemetry_events).
-- Run in Supabase SQL Editor after telemetry_events exists.

CREATE SCHEMA IF NOT EXISTS reporting;

CREATE TABLE IF NOT EXISTS reporting.weekly_location_performance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  location_id text NOT NULL,
  country text NOT NULL,
  week_start date NOT NULL,
  total_purchase_cost numeric NOT NULL DEFAULT 0,
  total_waste_cost numeric NOT NULL DEFAULT 0,
  waste_ratio numeric NOT NULL DEFAULT 0,
  stockout_events_count integer NOT NULL DEFAULT 0,
  price_alert_events_count integer NOT NULL DEFAULT 0,
  currency text NOT NULL,
  computed_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (location_id, week_start)
);

CREATE INDEX IF NOT EXISTS ix_weekly_location_performance_week
  ON reporting.weekly_location_performance (week_start);

CREATE INDEX IF NOT EXISTS ix_weekly_location_performance_country
  ON reporting.weekly_location_performance (country);

COMMENT ON TABLE reporting.weekly_location_performance IS
  'Weekly cost & waste KPIs per Brasaland location (CEO/Ops report). Upsert key: (location_id, week_start).';

-- Audit / observability of pipeline runs (Fase 3)
CREATE TABLE IF NOT EXISTS reporting.pipeline_run_log (
  run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  pipeline_name text NOT NULL,
  week_start date NOT NULL,
  status text NOT NULL,
  started_at timestamptz NOT NULL,
  finished_at timestamptz,
  rows_extracted integer NOT NULL DEFAULT 0,
  rows_upserted integer NOT NULL DEFAULT 0,
  error_message text,
  triggered_by text NOT NULL DEFAULT 'scheduler',
  checkpoint jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_pipeline_run_log_started
  ON reporting.pipeline_run_log (started_at DESC);
