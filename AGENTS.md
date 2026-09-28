Antes de comenzar a ejecutar nada debe leerse la memory bank,
Primero se leera el techContext.md
Luego se leera el projectbrief.md
Terminara leeyendo el progress.md
Quiero que a medida que se vaya trabajando se vaya actualizando el progress.md

## Reglas de estabilidad del monorepo (mantener main sano)

1. **Base siempre actualizada:** cada hito nuevo parte de `main` recién
   `git pull` (o de la rama del hito anterior **solo si** aún no está mergeada).
   No acumular trabajo sobre ramas feature abandonadas.
2. **Un hito → un PR → merge a `main`:** no dejar PRs draft eternamente; si el
   hito depende del anterior, mergear antes de abrir el siguiente.
3. **Tests del área antes del PR:** como mínimo
   `uv run pytest tests/pipelines/test_agent_*.py tests/pipelines/test_mcp_server.py -q`
   (y los del dominio tocado). Preferible rojo local que verde mentiroso.
4. **Deps solo con `uv add`:** nunca `pip install` directo en este monorepo.
5. **RAG vs memoria:** escrituras de memoria de agente **nunca** a colecciones
   `*_knowledge` / `brasaland_knowledge`. Namespace: `brasaland_agent_memory`.
6. **MCP vs herramientas directas:** el agente no debe llamar IncidentRepository
   ni ORM de inventario fuera del MCP Server.
7. **Memory bank al día:** actualizar `progress.md` (y techContext si cambia
   runtime) en el mismo PR del hito.
8. **Sin rutas dobles:** si se depreca un path (tools directos, etc.), debe
   fallar en duro — no convivir dos caminos al mismo backend.
