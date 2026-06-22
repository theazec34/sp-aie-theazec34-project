---
name: typescript-validation
description: Validation patterns for TypeScript domain models, inspired by dalestudy/skills@typescript and secondsky/claude-skills@zod.
source:
  - https://skills.sh/dalestudy/skills/typescript
  - https://skills.sh/secondsky/claude-skills/zod
---

# TypeScript Validation

## When to use
Use this skill when you need to:
- Define strict domain types in TypeScript.
- Implement validation rules with clear error details.
- Keep business rules and validators aligned.
- Convert generic demo code into business specific models.

## What this skill enforces
- One source of truth for model types.
- Explicit literal unions for status/category fields.
- Validation functions per entity returning structured errors.
- Rule parity with business context docs.

## Workflow
1. Read business context and extract entity fields.
2. Define interfaces and literal types.
3. Implement validators by entity.
4. Add consistency validators (dates, ranges, enums).
5. Validate with sample datasets and typecheck.

## Output expected
- Updated types file.
- Updated validations file.
- Demo/test data proving valid and invalid paths.
- No typecheck errors.

## Notes for this repo
Primary target files:
- src/types/models.ts
- src/utils/validations.ts
- src/demo.ts
