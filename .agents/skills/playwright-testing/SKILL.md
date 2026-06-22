---
name: playwright-testing
description: Pragmatic end-to-end test workflow for static sites and forms, inspired by mizchi/skills@playwright-cli.
source:
  - https://skills.sh/mizchi/skills/playwright-cli
---

# Playwright Testing

## When to use
Use this skill when you need confidence in:
- Core navigation routes and anchors.
- Menu rendering behavior.
- Form validation behavior.
- Mobile menu interactions.

## Core scenarios
- Home loads and key sections exist.
- Menu cards render with expected image count.
- Application form shows validation errors correctly.
- Header and footer links navigate to valid targets.

## Workflow
1. Start local server.
2. Add Playwright config and baseline tests.
3. Create smoke tests for home and application pages.
4. Add regression tests for critical user paths.
5. Run in CI friendly mode and report failures.

## Output expected
- tests/e2e/*.spec.ts files.
- Reproducible run command.
- Clear failure diagnostics.

## Notes for this repo
Suggested future command:
- npm run test:e2e
