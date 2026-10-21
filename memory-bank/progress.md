# Progress — Brasaland Digital

## Estado (2026-10-21)
- **`main`:** PRs **#1–#50** (pulido final mergeado).
- **Hotfix en curso:** Docker build Codespaces — `.dockerignore` bloqueaba `COPY data` / `docs/rfp` (`cursor/docker-ignore-build-fix-c620`).
- **Fuera de alcance:** `hito-3` Talent Pipeline / `3.5`.

## Hotfix Docker (actual)
- Causa: raíz `.dockerignore` tenía `docs` y `**/data` → build `worker`/`flower`/`backend` fallaba con `"/docs/rfp": not found`.
- Fix: excepciones para `data/`, `docs/company-knowledge-base/`, `docs/rfp/` (+ `*.md` de esas rutas).
- Nota demo: arrancar siempre desde la raíz del monorepo.

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
