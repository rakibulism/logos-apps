# Brands Logo — Figma plugin

Search 15,000+ SVG brand logos and drop them straight into Figma. The library is
fetched live from the [`brands-logo`](https://github.com/rakibulism/brands-logo)
repository, so it always reflects the current logos — no plugin update needed when
new ones are added.

## Features

- **Search & insert** — type a brand, click to drop the SVG onto the canvas.
- **Replace in place** — switch to *Replace* mode, select a layer, click a logo to
  swap it while keeping the original position and bounds.
- **Resize** — the selection strip shows the live width × height of the selected
  layer; edit them (with optional aspect-ratio lock) and hit **Apply**.
- **Auto-size readout** — selecting any layer or frame instantly reflects its size.
- **Appearance** — Light / Dark / Device default (follows Figma's theme), under the
  ⚙ settings icon.
- **Density** — Compact / Default / Large grid, also under settings.
- **About menu** — website link and the creator's X/Twitter (`@rakibulism`).

## How it syncs

The UI loads `assets/logos.json` and the individual SVGs from
`raw.githubusercontent.com/rakibulism/brands-logo/master/…`. Whenever
`python3 scripts/gen_site.py` regenerates the manifest (e.g. after adding logos or
running `scripts/sync_upstream_logos.sh`), the plugin picks the changes up on its
next load.

## Run it locally (development)

1. In the Figma **desktop app**: menu → **Plugins → Development → Import plugin from
   manifest…**
2. Select `figma-plugin/manifest.json` from this repo.
3. Run it from **Plugins → Development → Brands Logo**.

The plugin needs network access to `raw.githubusercontent.com` (already declared in
`manifest.json`).

## Publish to the Figma Community

Only the Figma account owner can publish:

1. Right-click the plugin in **Plugins → Development → Brands Logo → Publish new
   release…**
2. Fill in name, description, icon and cover art, then submit for review.
3. Once live, update the **Install in Figma** button URL on the website
   (`scripts/site_template.html`, the `__PLUGIN_URL__` placeholder / `data-plugin-url`)
   with the real `figma.com/community/plugin/…` link.

## Files

| File | Role |
|------|------|
| `manifest.json` | Plugin manifest (entry points + allowed domains) |
| `code.js` | Main thread — creates/replaces/resizes nodes via the Figma API |
| `ui.html` | Plugin UI — search, grid, settings, menu (self-contained) |
