---
name: mock-data
description: Generate realistic demo entries that match the shapes already defined in frontend_rebuild/src/lib/demo-data.ts (or frontend/src/lib/demo-data.ts when working in the older directory). Use when the user asks to seed, add, generate, or expand demo data — teams, users, courses, scores, volunteers, certificates, etc.
---

# /mock-data

Generate demo data that matches the existing shapes in `frontend_rebuild/src/lib/demo-data.ts` (or `frontend/src/lib/demo-data.ts` when working in the older directory).

## When to use

Trigger when the user asks to:

- "Add more teams / users / scores / etc."
- "Seed the demo with realistic data."
- "Generate 20 mock entries for X."
- "Expand demo-data.ts."

If the user just wants a one-off mock for a single page, answer inline without invoking this skill.

## Required inputs

Ask only if missing:

- **Target file** — defaults to `frontend_rebuild/src/lib/demo-data.ts`. If the shape exists in `frontend/`, ask which one to update.
- **Entity** — which collection to expand (e.g. `teams`, `users`, `judges`, `volunteers`, `events`, `courses`, `scores`).
- **Count** — how many entries.
- **Realism constraints** — names from a specific pool, ID format, date range, etc. Defaults to: Bangladeshi names for users, `PS26-CSE<course>-<3-digit>` team codes, ISO date strings, scores in 0–100 range.

## Steps

1. **Read the current file** to find the relevant export and its TypeScript shape. Don't change shapes — only add entries.
2. **Find the matching type** in `frontend_rebuild/src/types/` (or inline in demo-data.ts if types are co-located).
3. **Generate entries** that:
   - Match the existing shape exactly (field names, casing, optional vs required).
   - Use plausible values — no `lorem ipsum`, no duplicate IDs, no copy-pasted rows with field swaps.
   - Reference other entities consistently (a team's course ID must exist in the courses array; a volunteer's floor must exist in the floors array).
4. **Insert in the right place** — append to the existing array, preserving order. Don't reorder or remove entries.
5. **Preserve cross-references** — if the data references IDs or codes, use real values from the existing arrays, not invented ones.

## Patterns to follow

- **IDs**: keep the existing prefix convention. Examples already in use: `PS26-CSE220-001`, `VOL26-F2-001`, `COURSE-CSE220`.
- **Names**: use a mix of Bangladeshi first/last names consistent with UIU's student/faculty context. Vary across entries — don't repeat the same name twice.
- **Dates**: ISO 8601 strings (`YYYY-MM-DD`). Keep them within the project's event window (see existing entries).
- **Scores**: integers or floats in the same range as existing entries. Keep decimal precision consistent.
- **Status fields**: pick from the existing string-union types already defined in the file.

## Output checklist

Before finishing:

- [ ] No duplicate IDs/codes.
- [ ] All cross-references resolve to existing entries.
- [ ] TypeScript types still compile (no `any`, no missing required fields).
- [ ] New entries are inserted in the correct array, not at the top.
- [ ] File size impact noted if you added >50 entries.

## Reporting back

Report:

- File path updated.
- Number of entries added per array.
- Any cross-references that needed to be invented (and what you used).
- File size delta (rough line count).