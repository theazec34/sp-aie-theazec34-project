# Progress — Brasaland Digital

## Estado (2026-10-21)
- **`main`:** PRs **#1–#51** (Docker ignore #51 mergeado).
- **Hotfix en curso:** seed admin — `admin@brasaland.local` rechazado por EmailStr (`cursor/seed-admin-email-fix-c620`).
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Hotfix seed email (actual)
- Causa: `email-validator` rechaza TLD `.local` → `seed_auth` tumba backend/worker/flower en bucle.
- Fix: `.env.example` → `SEED_ADMIN_EMAIL=admin@brasaland.com`.
- Demo Codespaces: editar `.env` y `docker compose up --build` de nuevo.

## Hotfix Docker (#51)
- Causa: `.dockerignore` excluía `docs` / `**/data` → `COPY docs/rfp` fallaba.
- Fix: excepciones para `data/`, `docs/company-knowledge-base/`, `docs/rfp/`.

## Pulido final (#50)
- Review: `docs/PROJECT_REVIEW_FINAL.md`
- Fix: `skipAuth` incidencias + login → `/`
- Visual: backoffice carbón/brasa; hero web full-bleed con marca; copy ES

## Hitos en main
| Área | PR |
|------|-----|
| … | #1–#48 |
| NIST CSF practices | #49 |
| Pulido final UI/review | #50 |
