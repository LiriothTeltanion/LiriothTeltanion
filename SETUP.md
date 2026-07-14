# GitHub profile repository setup

This repository powers the public GitHub profile for **Kevin Cusnir — Lirioth
Teltanion**. GitHub renders the root `README.md` directly on the
`LiriothTeltanion` account profile.

## Prerequisites

- Git.
- PowerShell 7 or Windows PowerShell 5.1.
- Write access to `LiriothTeltanion/LiriothTeltanion` only when publishing.

No package installation or build step is required. The public profile uses
Markdown, HTML and repository-local image assets.

## Get a working copy

```powershell
git clone https://github.com/LiriothTeltanion/LiriothTeltanion.git
Set-Location .\LiriothTeltanion
git status --short --branch
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\profile\verify-profile.ps1
```

Keep one editable clone as the source of truth. Use `git rev-parse --show-toplevel`
whenever there is doubt about which copy is open.

See [the folder map](docs/profile-maintenance/FOLDER_MAP.md) for the maintained
repository structure.

## Safe editing cycle

1. Read `AGENTS.md` and check `git status`.
2. Inspect the exact README section and every asset it references.
3. Define the smallest coherent change.
4. Before a major README restructure, create a local backup:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\profile\backup-readme.ps1
   ```

5. Make the targeted edit without replacing unrelated content.
6. Follow the validation and visual-review steps in
   [the maintenance workflow](docs/profile-maintenance/WORKFLOW.md).

Backups are written to `.local-backups/`. The tracked `.gitignore` keeps that
directory local in every clone.

## Asset conventions

- Keep README asset paths relative, with their existing case and directory.
- Do not rename or delete files in `assets/` or `preview/` without an explicit
  reference and retention audit.
- Keep animated visuals paired with an appropriate static or reduced-motion
  experience.
- Preserve meaningful alt text and verify both desktop and narrow/mobile
  rendering after a visual change.
- Preserve the English, Spanish and Hebrew sections unless a task explicitly
  updates all affected translations.

`preview/` is a tracked review archive, not a disposable cache. Its retention
rules are documented in the maintenance workflow.

## Optional dynamic visuals

The public profile intentionally favors stable local assets. The contribution
snake is an opt-in workflow template and is not active while it remains under
`extras/`. See
[Optional dynamic contribution animation](extras/OPTIONAL-DYNAMIC-VISUALS.md)
before enabling it.

## Publish only after review

Publishing is a deliberate manual step. Stage only the files that belong to the
approved change:

```powershell
git status --short
git diff --check
git add -- SETUP.md docs/profile-maintenance/WORKFLOW.md
git diff --cached
git commit -m "docs: describe the focused profile change"
git push
```

Replace the example paths with the exact files in the approved change. Do not
commit or push from an automated editing session unless Kevin explicitly
requests it. After publishing, open the public profile and inspect its desktop
and mobile rendering.
