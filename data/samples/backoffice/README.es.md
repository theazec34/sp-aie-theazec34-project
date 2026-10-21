# Muestras para probar el backoffice

| Archivo | Módulo | Uso |
|---------|--------|-----|
| `reserva-ejemplo.json` | Reservas web | `POST /reservations` o formulario `:3000/reservas` |
| `candidatura-ejemplo.json` | Candidaturas | Referencia de campos; alta vía `/trabaja-con-nosotros` |
| `cv-luis-herrera-demo.txt` | Candidaturas | “CV” de ejemplo (renómbralo a `.pdf` si quieres) |
| `incidencia-ejemplo.json` | Registrar incidencia | Campos del formulario `/incidents/nueva` |
| `incidents-demo.csv` | Panel / seed | `python scripts/seed_incidents.py data/samples/backoffice/incidents-demo.csv` |
| `proveedor-ejemplo.json` | Proveedores | Referencia de alta |
| `consulta-rag-ejemplos.txt` | Base de conocimiento | Preguntas listas |
| `chat-agente-ejemplos.txt` | Agente de soporte | Mensajes de prueba |

## RFP (PDF listos)

Están en `rfp-requests/brasaland/`:

- `brasaland-request-1.pdf` — formal (aceptar)
- `brasaland-request-2.pdf` — informal (aceptar)
- `brasaland-request-3.pdf` — inválido (rechazar)

Súbelos en backoffice → **Recepción de RFP**.

Guía completa: [`docs/backoffice/GUIA-MODULOS.es.md`](../../../docs/backoffice/GUIA-MODULOS.es.md).
