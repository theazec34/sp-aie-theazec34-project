-- Celery dead-letter queue records (DEV-55)
-- Also auto-created via SQLModel metadata.create_all when workers run.

CREATE TABLE IF NOT EXISTS celery_dead_letters (
    id              TEXT PRIMARY KEY,
    task_id         TEXT NOT NULL,
    task_name       TEXT NOT NULL DEFAULT '',
    attempt         INTEGER NOT NULL DEFAULT 0,
    error_message   TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_celery_dead_letters_task_id
    ON celery_dead_letters (task_id);
