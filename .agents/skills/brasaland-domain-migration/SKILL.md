---
name: brasaland-domain-migration
description: Custom skill to migrate this repository from election domain types to Brasaland business entities and reports.
source:
  - local-custom
---

# Brasaland Domain Migration (Custom)

## Purpose
This custom skill aligns TypeScript code with the official business context in Brasaland.md.

## Required entities
- EncargoProveedor
- PlatoCarta
- ReservaMesa
- PedidoDomicilio

## Validation requirements
Implement rules exactly as documented:
- ISO date/date-time checks where required.
- Numeric range checks (non-negative, limits, integer constraints).
- Literal enum checks for status/category/platform fields.
- Trimmed non-empty string checks.

## Required reports
- EncargoProveedor: count by estado, sum and average importeTotal by estado.
- PlatoCarta: active count by categoria, and sum/avg/min/max precio by categoria (only active).
- ReservaMesa: count by estado, sum numeroComensales for confirmada.
- PedidoDomicilio: count by plataforma, sum importeTotal by plataforma excluding cancelado.

## Workflow
1. Replace election oriented types with Brasaland domain types.
2. Replace election oriented validators with Brasaland validators.
3. Update demo data and report examples to Brasaland entities.
4. Typecheck and run demo output checks.
5. Update memory-bank/progress.md with migration status.

## Target files
- src/types/models.ts
- src/utils/validations.ts
- src/utils/transformations.ts (if needed for report helpers)
- src/demo.ts
- memory-bank/progress.md
