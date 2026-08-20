# Portfolio (`/portfolio`)

The structured professional portfolio / CV archive for **jespyucha.com**, reached from the
site-wide **Portfolio** nav link.

- **jespyucha.com** — the broader Jespyucha platform (home, trading, markets, articles, academic).
- **jespyucha.com/portfolio** — the professional record: experience, projects, research, education, skills, writing, contact, CV.

## What it is / how it relates to the site
A single self-contained page (`portfolio/index.html`) that visually belongs to jespyucha.com —
it reuses the same Tailwind config, colour tokens (`paper/charcoal/ink/trustBlue/traderGreen`),
system-font stack, and dark-mode behaviour (`localStorage['theme']`, `.dark` on `<html>`).

Layout: a persistent two-pane view on desktop (sticky left identity + section nav, scrolling
right content), collapsing to a single column on mobile (identity → nav → content). Sections
switch via hash routing (`/portfolio#experience`, `#projects`, `#research`, …) with **no page
reload**. One shared, accessible modal powers project/research details and the CV viewer
(closes on **Close**, **backdrop click**, or **Esc**; focus-trapped).

## Structure
| Section | Source of truth |
|---|---|
| About · In Brief · Experience · Education | CV (`Ashok_Sunuwar_Resume.pdf`) |
| Projects · Research & Analysis | CV + `assets/docs/*.docx` |
| Skills | grouped from evidenced work in the CV |
| Writing · Contact | links to existing site sections |
| CV | `assets/cv.pdf` (phone-redacted copy) |

## Technologies
Static HTML + CSS + minimal vanilla JavaScript. Tailwind via the same CDN the rest of the site
uses. No framework, no build step. All portfolio CSS is namespaced under `.pf` so it cannot
affect other pages.

## How to update content
All content is plain HTML inside `portfolio/index.html`.

- **Add / edit a project:** copy an existing `<article>` in the `#projects` section, and (for the
  modal) copy a matching hidden `<div id="detail-...">` block. Point the card's
  `data-detail="detail-yourid"` at it. Only include fields (Objective / Approach / Tools /
  Outcome / Links) that have real information.
- **Add / edit research:** same pattern in the `#research` section.
- **Replace the CV:** overwrite `assets/cv.pdf`. Keep it **web-safe** (no personal phone number —
  the published copy is redacted; regenerate the redaction if you replace it).
- **Add photos/videos:** add a new `<section id="...">` + a matching nav link in the left pane,
  and a modal detail block if needed. Only add these sections if you actually have the media.
- **Add languages:** add a `#languages` section + nav link (plain list, e.g. `English — Professional`).

## How to publish / update
The site is static GitHub Pages (repo `jespyucha/my-website`, custom domain via `CNAME`,
`.nojekyll`). Commit the changed files and push to `main`; Pages redeploys automatically.
`portfolio/index.html` serves at the clean URL `/portfolio`.

## Implementation notes
- The homepage's old placeholder "Selected Work" (`#work`) section was removed; the Portfolio
  nav link across all pages now points to `/portfolio`.
- Nothing else on the site (hero, footer, typography, theme, other pages/URLs) was changed.
- Honesty labels in the content: the Prime Intelligence internship is marked **Incoming** (role
  scope, not achievements); the BCG/Forage item is marked a **virtual job simulation**; the
  organisational-behaviour work is framed as a **research proposal / theoretical contribution**.
