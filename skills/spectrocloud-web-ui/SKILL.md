---
name: spectrocloud-web-ui
description: "Spectro Cloud brand theming for anything rendered in a browser -- CSS custom properties for the 2025 palette, Plus Jakarta Sans, buttons/cards/tables/nav, dark mode, responsive breakpoints, accessibility. Use when Craig asks for a web page, dashboard, portal, demo app, HTML artifact, or status/monitoring view that should look like Spectro Cloud: make it look nice and legible, make it spectro branded, use our branding, keep it simple and clear, a terminal-style window showing errors, a customer-facing landing or portal page, a hello-universe style demo. Also use before hand-rolling any colors or fonts in an HTML deliverable for a customer, and pair it with spectrocloud-brand for logo rules and messaging. Not for slide decks or PDFs."
---

# Spectro Cloud Web UI Theming

Brand-aligned web UI patterns for dashboards, internal tools, customer portals, and demo apps. READ the `spectrocloud-brand` skill for full color definitions, logo rules, and messaging guidelines -- this skill focuses on web implementation.

## When to Use

- Building web dashboards or admin panels with SC branding
- Creating demo apps (e.g., hello-universe style demos)
- Internal tools that need brand-consistent styling
- Customer-facing portals or landing pages
- Any HTML/CSS project requiring SC visual identity

## CSS Custom Properties

Import the full palette. These mirror the definitions in `spectrocloud-brand/references/colors.md` -- if the two ever disagree, colors.md wins.

```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200;300;400;500;600;700;800&display=swap');

:root {
  /* Primary */
  --sc-teal: #1F7A78;
  --sc-teal-dark: #005B5B;
  --sc-teal-darker: #004244;
  --sc-teal-darkest: #043736;
  --sc-green: #9EB277;
  --sc-green-dark: #5D823C;
  --sc-gold: #F0BE65;
  --sc-gold-dark: #DE8D2A;
  --sc-orange: #B94B01;
  --sc-orange-dark: #851A01;
  --sc-lilac: #7E5C8E;
  --sc-lilac-dark: #441647;

  /* Neutrals */
  --sc-paper: #F7F1ED;
  --sc-neutral-1: #E0DCD7;
  --sc-neutral-2: #BEB9B6;
  --sc-neutral-3: #9E9C9C;
  --sc-neutral-4: #3C4949;
  --sc-neutral-5: #1E3332;
  --sc-ink: #012121;

  /* Semantic aliases */
  --sc-bg: var(--sc-paper);
  --sc-text: var(--sc-ink);
  --sc-text-muted: var(--sc-neutral-4);
  --sc-border: var(--sc-neutral-2);
  --sc-border-light: var(--sc-neutral-1);
  --sc-primary: var(--sc-teal);
  --sc-primary-dark: var(--sc-teal-dark);
  --sc-accent: var(--sc-gold);
  --sc-success: var(--sc-green);
  --sc-warning: var(--sc-gold-dark);
  --sc-danger: var(--sc-orange);

  /* Typography */
  --sc-font: 'Plus Jakarta Sans', 'Trebuchet MS', sans-serif;
  --sc-font-size-base: 16px;
  --sc-line-height: 1.6;

  /* Spacing scale */
  --sc-space-xs: 4px;
  --sc-space-sm: 8px;
  --sc-space-md: 16px;
  --sc-space-lg: 24px;
  --sc-space-xl: 32px;
  --sc-space-2xl: 48px;

  /* Border radius */
  --sc-radius-sm: 4px;
  --sc-radius-md: 8px;
  --sc-radius-lg: 12px;
}
```

## Typography Setup

Weight hierarchy for web (from spectrocloud-brand):

| Element | Weight | CSS |
|---------|--------|-----|
| Display / hero headings | 200 ExtraLight | `font-weight: 200` |
| Section headings (h2-h3) | 500 Medium | `font-weight: 500` |
| Body text | 400 Regular | `font-weight: 400` |
| Blockquotes | 300 Light | `font-weight: 300` |
| Labels, badges, nav items | 600 SemiBold | `font-weight: 600` |
| Small-text emphasis | 700 Bold | `font-weight: 700` |

## Base Styles

```css
*, *::before, *::after { box-sizing: border-box; }

body {
  font-family: var(--sc-font);
  font-size: var(--sc-font-size-base);
  line-height: var(--sc-line-height);
  color: var(--sc-text);
  background: var(--sc-bg);
  margin: 0;
}

h1 { font-weight: 200; font-size: 2.5rem; color: var(--sc-teal-darkest); }
h2 { font-weight: 500; font-size: 1.75rem; color: var(--sc-teal-dark); }
h3 { font-weight: 500; font-size: 1.25rem; color: var(--sc-ink); }
h4 { font-weight: 600; font-size: 1rem; color: var(--sc-ink); }

a { color: var(--sc-teal); text-decoration: underline; }
a:hover { color: var(--sc-teal-dark); }

code {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  background: var(--sc-neutral-1);
  padding: 2px 6px;
  border-radius: var(--sc-radius-sm);
  font-size: 0.9em;
}

pre code {
  display: block;
  padding: var(--sc-space-md);
  overflow-x: auto;
  border-left: 3px solid var(--sc-teal);
}
```

## Component Library

Copy-paste HTML/CSS for every `sc-*` component lives in **`references/components.md`**:

| Component | Classes |
|-----------|---------|
| Navigation bar | `.sc-navbar`, `.sc-navbar-brand`, `.sc-navbar-link` |
| Side navigation | `.sc-sidenav`, `.sc-sidenav-section`, `.sc-sidenav-link` |
| Cards | `.sc-card` (+ `--gold` / `--lilac` / `--orange` variants) |
| Stat / KPI cards | `.sc-stat-card`, `.sc-stat-value`, `.sc-stat-change` |
| Tables | `.sc-table` |
| Buttons | `.sc-btn-primary`, `.sc-btn-secondary`, `.sc-btn-accent` |
| Badges / pills | `.sc-badge` (+ color variants) |
| Alerts | `.sc-alert` (+ `--success` / `--warning` / `--error`) |
| Form inputs | `.sc-input`, `.sc-label` |
| Footer | `.sc-footer` |
| Dark mode overrides | `[data-theme="dark"]` block |
| Responsive breakpoints | 576 / 768 / 1024 / 1280px, mobile-first |
| Animation | `.sc-fade-in` |

Key patterns baked into the components: navbar uses knockout-white logo on teal; sidenav and footer sit on Ink with Gold active/link accents; cards get a 3px teal top border; stat values use the 200 ExtraLight display weight.

## Dark Mode

Apply via `[data-theme="dark"]` or `@media (prefers-color-scheme: dark)` -- the override block is in `references/components.md`. Backgrounds swap to Ink/neutral-5, never blue/purple.

On Ink backgrounds, use Gold (#F0BE65, 9.88:1) or Green (#9EB277, 7.32:1) for high-contrast text. Teal, Orange, and Lilac are only AA-large on dark -- use for decorative accents, not body text.

## Animation Guidelines

Follow the spectrocloud-brand animation principles:

- **Transitions**: 150-300ms ease-out for UI interactions (hovers, focus, toggles)
- **Page transitions**: 300-500ms ease-in-out for route changes or panel slides
- **Folding motifs**: Use subtle `transform: rotateY()` or skew effects to suggest origami folds -- keep it tactile and gentle, never bouncy or playful
- **No character-by-character text animation** -- fade or slide entire blocks
- **Product demos**: Keep the UI feature front and center, minimize surrounding motion

## Accessibility

WCAG contrast ratios from the brand guide (see spectrocloud-brand for full grid):

**On Paper backgrounds (#F7F1ED):** Dark Lilac (12.92:1), Dark Teal (11.69:1), Dark Orange (8.74:1) all pass AAA. Teal and Lilac (4.93:1) pass AA for normal text.

**On Ink backgrounds (#012121):** Gold (9.88:1) and Green (7.32:1) pass AAA. Orange, Teal, and Lilac only pass AA-large (~3.3:1).

Rules:
- Use `--sc-teal-darkest` or `--sc-ink` for body text on light backgrounds
- Use `--sc-gold` or `--sc-green` for body text on dark backgrounds
- Interactive elements need visible `:focus` styles (the `box-shadow` on `.sc-input:focus` in components.md is the pattern to follow)
- Minimum touch target: 44x44px for mobile
- Always provide `alt` text on logo images

## Files

- `references/components.md` -- full `sc-*` component CSS/HTML library
