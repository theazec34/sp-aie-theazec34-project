# sp-aie-theazec34-project — Brasaland Digital

Guía completa: **[PROJECT.md](./PROJECT.md)** · Docker: **[DOCKER.md](./DOCKER.md)** · English overview: **[README.md](./README.md)**

## Puertos

| Puerto | Servicio | Comando |
|--------|----------|---------|
| 3000 | Website | `cd uis/website && npm run dev` |
| 3001 | Backoffice | `cd uis/backoffice && npm run dev` |
| 8000 | API | `cd services/api && uv run uvicorn app.main:app --reload --port 8000` |

O `docker compose up --build` desde la raíz.
