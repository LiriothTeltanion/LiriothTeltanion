# Public asset manifest

This manifest records which visual files are part of the public profile, which
files are retained as review or provenance material, and which legacy captures
were intentionally removed. It is a maintenance policy, not a license to prune
files that are not currently linked.

## Public README assets

The following families are referenced by both `README.md` and
`README_EXPANDED.md`. Their relative filenames and letter case are public API.

| Profile surface | Public files |
| --- | --- |
| Identity banner | `profile-banner-animated.svg`, `profile-banner-static.svg`, `profile-banner-mobile-animated.svg`, `profile-banner-mobile-static.svg` |
| Personal signature | `brand/kc-lt-signature-animated.svg`, `brand/kc-lt-signature.svg` |
| Nova Music Lab live preview | `nova-music-live-preview.jpg`, `nova-music-live-preview-mobile.jpg` |
| Nova Music Lab journey | `nova-music-journey-animated.svg`, `nova-music-journey-static.svg`, `nova-music-journey-mobile.svg`, `nova-music-journey-mobile-static.svg` |
| NovaFit evidence | `novafit-product-tour.gif`, `novafit-product-tour-static.png`, `analytics-training-atlas.png`, `theme-spectrum.png`, `novafit-trust-system-animated.svg`, `novafit-trust-system-mobile.svg` |
| Engineering and growth | `engineering-orbit-animated.svg`, `engineering-orbit-mobile.svg`, `engineering-orbit-mobile-static.svg`, `learning-roadmap-animated.svg`, `learning-roadmap-mobile.svg` |
| Global journey atlas | `world-globe-animated.svg`, `world-globe-static.svg`, `world-globe-mobile.svg`, `world-globe-mobile-static.svg` |

Before changing this table, regenerate the READMEs when appropriate and verify
the real references in both variants. The repository validator remains the
authoritative check for missing local assets.

## Generated and provenance assets

- `tools/profile/generate_world_globe.py` is the reproducible source for the
  four global journey atlas SVGs. It uses pinned Natural Earth public-domain
  data and writes both animated and reduced-motion variants. Its explicit
  coverage contract represents all 195 baseline sovereign states: 182 through
  the pinned Natural Earth polygon/tiny layers and 13 omitted microstate/island
  states through deterministic labeled centroid markers. Six clustered eastern-
  Caribbean markers use small callout offsets and leader lines so each remains
  individually visible while its true geographic anchor is preserved.
- `assets/projects/` retains project-card source and raster variants. They are
  useful provenance for future profile layouts even when the current README
  presents the projects directly.
- The four `portfolio-command-center-*.svg` files are retained layout
  provenance. They were removed from the recruiter-first README to bring the
  flagship project above the fold, not because the artwork became disposable.
- `assets/brand/` contains the master, animated, compact, light, monochrome and
  transparent PNG versions of the KC × LT signature plus the optimized avatar
  cameo embedded by the four responsive banner variants. Profile 2.0 refines
  the same blue handwritten mark for faster KC × LT recognition; it does not
  replace Kevin Cusnir or Lirioth Teltanion with an unreadable symbol.
- `assets/novafit-product-tour.gif` is the Profile 2.0 desktop motion proof for
  NovaFit 4.2.0. `assets/novafit-product-tour-static.png` is the canonical mobile
  and reduced-motion fallback. Both must tell the same recruiter-facing story,
  use clearly labeled seeded demo profiles and deterministic synthetic records,
  and exclude real wellness history, runtime databases, secrets and private
  exports.
- `assets/motivation-center-animated.svg` and
  `assets/motivation-center-mobile.svg` remain reusable NovaFit visual-system
  provenance. Profile 2.0 replaces their README slot with the more complete
  product tour; they are preserved rather than deleted.
- `assets/visuals/` and the remaining unlinked root-level SVG/PNG files retain
  prior section artwork and source evidence. Unlinked does not mean obsolete.
  Audit references, provenance and visual value before proposing removal.

Generated output must remain deterministic, accessible and free of real private
records. Any personal-looking demonstration field must be visibly identified as
seeded public demo data. When a generator exists, update the generator before
mechanically rebuilding its output.

## Upload-ready social previews

`assets/social/` contains editable 1280 × 640 SVG sources and matching PNGs for
the profile, Nova Music Lab, NovaFit, Christopher Rodríguez Portfolio and
Fullstack2026. They are tracked preparation assets; GitHub does not use them
until the matching PNG is uploaded manually in the target repository settings.

The exact repository-to-file mapping and publication order live in
`PUBLIC_METADATA.md`. Keep the SVG and PNG pairs together, preserve the verified
claims in their text and confirm dimensions before any upload.

## Retained preview archive

Every file under `preview/` is a tracked rendering proof or historical visual
snapshot. The archive is deliberately retained even when a file is not linked
from the current README.

- Never delete, rename, recompress or overwrite a preview during unrelated
  cleanup.
- `.nova-pack-backup/` is not part of this archive. It is an ignored local
  package-snapshot path and must not be committed.
- A future preview reduction requires an explicit task, a reference and
  historical-value audit, and Kevin's approval.

## Removed privacy-risk legacy captures

The following unreferenced NovaFit captures were removed from the tracked tree
because they displayed Kevin/Lirioth alongside wellness-style metrics and were
not required by the public profile:

- `assets/novafit-ultimate-gui.png`
- `assets/novafit-analytics-tour.gif`
- `assets/novafit-command-center.png`
- `assets/novafit-gui-definitive.png`
- `assets/motivation-center-ultimate.png`
- `assets/multi-profile-language-center.png`
- `assets/sport-data-coach-real.png`

Their filenames may remain in negative regression assertions that prevent them
from being reintroduced into generated profile content. Do not restore these
captures without a fresh privacy review and explicit approval.

Kevin confirmed on 2026-07-15 that the historical values in those captures were
synthetic demonstration data, not private wellness records. The files remain
removed from the current profile because they are obsolete and unreferenced,
but their presence in earlier Git history does not require a destructive
history rewrite.

## No-delete-without-audit policy

Before deleting any asset:

1. Search the full tracked tree, README generator, documentation, CSS/SVG
   references and tests for the exact filename and stem.
2. Distinguish public runtime use, generated output, provenance material and
   retained preview history.
3. Inspect the visual for identity, privacy and evidence value.
4. Record the intended removal in this manifest when it affects a public or
   deliberately retained asset family.
5. Run the profile validator, tests and `git diff --check`, then review every
   deletion in `git status --short`.

When evidence is ambiguous, preserve the file and request direction.
