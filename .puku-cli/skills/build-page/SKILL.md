---
name: build-page
description: Scaffold a new portal page under frontend_rebuild/src/app/<portal>/... with shadcn layout, brand styling, and mock-data wiring. Use when the user asks to create, build, add, or scaffold a new page, route, or screen in any portal (admin, coordinator, faculty, club, team, volunteer, public, login, or root).
---

# /build-page

Scaffold a Next.js App Router page in `frontend_rebuild/src/app/<portal>/<path>/page.tsx` with shadcn/ui layout, brand styling, and mock-data wiring.

## When to use

Trigger this when the user says "build a page", "add a page", "scaffold a route", "new screen for X portal", or anything similar about creating a portal page.

## Required inputs

If the user didn't specify, ask one focused question to fill the gaps:

- **Portal** — one of: `admin`, `coordinator`, `faculty`, `club`, `team`, `volunteer`, `public`, `login`, or root `(root)`.
- **Page name** — kebab-case slug (e.g. `audit-logs`).
- **Purpose** — one-line description of what the page does.

If portal and purpose are clear from context, skip the question.

## Steps

1. **Confirm the target path**: `frontend_rebuild/src/app/<portal>/<page>/page.tsx`. If portal is `root`, use `frontend_rebuild/src/app/(root)/<page>/page.tsx` — but only create the route group if it doesn't already exist.
2. **Check existing layout**: if `frontend_rebuild/src/app/<portal>/layout.tsx` exists, the page inherits the portal shell (header, sidebar) automatically — don't add another shell. If no layout exists, scaffold a minimal one with the PortalShell from `frontend_rebuild/src/components/shared/`.
3. **Page structure** — every page must include:
   - Default export named after the page (e.g. `AdminAuditLogsPage`).
   - `metadata` export with a meaningful title.
   - A `<PageHeader>` component (from `components/shared/`) with title + description + optional primary action button.
   - The main content rendered inside the layout's content area.
4. **Styling rules**:
   - Use shadcn/ui primitives from `frontend_rebuild/src/components/ui/` — `Card`, `Button`, `Table`, `Dialog`, `Tabs`, `Badge`, `Input`, etc.
   - Tailwind utility classes only. Use the `brand` color scale for accents (orange 500/600 for primary actions).
   - Typography: `font-sans` (Sour Gummy → Inter fallback). Display headings may use `font-brand` (McLaren) for hero/title moments only — never for body text.
   - Use the existing `cn()` helper from `frontend_rebuild/src/lib/utils.ts` for conditional classes.
5. **Mock data**:
   - Pull demo entries from `frontend_rebuild/src/lib/demo-data.ts` if the relevant export exists. Add new exports there if the shape doesn't exist yet.
   - Wrap in a small typed helper at the top of the file or a `useState` hook — don't pull from a real backend.
6. **Interactive bits**: dialogs, dropdowns, and form fields use the Radix primitives already wired up. Don't introduce new state libraries.
7. **No `any`**: type the props with the existing `types/` module if available.

## Output checklist

Before finishing, the page should:

- [ ] Compile under `tsc --noEmit` (no TS errors).
- [ ] Render without runtime errors when navigating to the route.
- [ ] Match the visual language of existing pages in the same portal.
- [ ] Have working empty/loading/error states for any async-ish data (use `useState` + simulated delay, or just a static placeholder).
- [ ] Have a meaningful `metadata.title`.

## Reporting back

Report only:

- The file path created.
- Any new mock-data exports added (with their shapes).
- Anything you had to assume (e.g. "assumed the page lists teams — flag if you wanted a different layout").