---
applyTo: "src/atwood/templates/**/*.html,src/atwood/static/**/*.{css,js}"
---

# Frontend instructions

- The MapLibre map and settings panel are server-rendered Jinja templates in
  `src/atwood/templates/`; local Bootstrap and custom assets are in
  `src/atwood/static/`.
- Preserve element IDs, `data-bs-*` attributes, ARIA attributes, local-storage
  keys, endpoint paths, and MapLibre layer/source identifiers unless the
  corresponding JavaScript is updated in the same change.
- Keep the map usable at all viewport sizes. The settings panel overlays the
  map and must not permanently shrink its available map viewport.
- Use existing Bootstrap assets and `custom.css` for visual work. Do not add a
  frontend framework, build pipeline, or external UI library without an
  explicit request.
- For settings-area design changes, use the `web-designer` agent before
  implementation and keep form labels, keyboard navigation, focus indicators,
  contrast, and live feedback accessible.
