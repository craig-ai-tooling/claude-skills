# Puppeteer HTML→PDF Rendering (shared reference)

Canonical render guidance for all Puppeteer-based Spectro Cloud document generators (`exec-doc-generator`, `slide-deck-generator`). If a SKILL.md and this file ever disagree, this file wins.

## Non-negotiable rules

1. **Fonts load via `<link>` tags in `<head>` — NEVER `@import` inside `<style>`.** `@import` silently fails in Puppeteer PDF rendering and everything falls back to Trebuchet MS.

   ```html
   <link rel="preconnect" href="https://fonts.googleapis.com">
   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
   <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200;300;400;500;600;700;800&display=swap" rel="stylesheet">
   ```

2. **`-webkit-print-color-adjust: exact`** on the page/slide root — without it backgrounds and brand colors drop out of the PDF.

3. **`waitUntil: 'networkidle0'`** on `page.goto` — gives Google Fonts time to load before render.

4. **All CSS inline in one `<style>` block** (no external stylesheets except the font `<link>`).

## Emoji centering

Emojis have inconsistent vertical metrics across fonts/platforms in Puppeteer. When using emojis as icons, wrap them in a flex container with explicit sizing:

```css
.icon-wrap {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; line-height: 1;
  flex-shrink: 0;
}
```

Do NOT rely on `vertical-align` or bare emoji text for alignment. For circular icon backgrounds, add `border-radius: 50%; background: var(--accent-glow);` to the wrapper.

## SVG letter counters (compound paths required)

Letters with enclosed counters (p, o, e, d, b, a, g, C) need the outer shape and inner hole as **subpaths within the same `<path>` element** (compound paths). If they are separate `<path>` elements, the holes render as solid fill in Puppeteer regardless of `fill-rule`.

- **USE** the Brand Drive SVGs (viewBox `0 0 501 192`, compound paths):
  - `spectrocloud-logo-horizontal-knockout-white.svg` (dark backgrounds, `fill="#fff"`)
  - `spectrocloud-logo-horizontal-currentcolor.svg` (light backgrounds, `fill="currentcolor"` — set CSS `color` on the SVG to control it)
- **NEVER** use the old website SVG `spectrocloud-logo-horizontal.svg` (viewBox `0 0 148 57`) for Puppeteer/PDF output — separate paths per letter part, counters fill solid.
- Both good variants MUST carry `fill-rule="evenodd"` on the `<svg>` element.
- READ and inline the SVG file contents into the HTML — never `<img src>` a relative path (the PDF renders from `file://` and paths break when the HTML moves).

## Page breaks

- Paged docs: give each page wrapper `break-inside: avoid` protection via an `@media print` block (`break-inside: avoid` on cards/banners, `break-after: avoid` on section titles).
- Slide decks: each `.slide` gets `page-break-after: always` except the last.

## generate-pdf.mjs

Don't retype the render script — run the one each skill ships. Ensure `puppeteer` is installed (`npm install puppeteer`) before generating.

- **Letter-format document (exec docs):** `node exec-doc-generator/assets/generate-pdf.mjs <input.html> <output.pdf>`
- **16:9 slide deck:** `node slide-deck-generator/assets/generate-pdf.mjs <input.html> <output.pdf>`

Both take the input HTML path and desired output PDF path as arguments and print `usage: ...` to stderr and exit 1 if either is missing. They differ only in `page.pdf()` options: the exec-doc script uses `format: 'letter'` with small margins; the slide-deck script sets a `1280x720` viewport and calls `page.pdf` with matching `width`/`height`, `landscape: true`, and zero margins.
