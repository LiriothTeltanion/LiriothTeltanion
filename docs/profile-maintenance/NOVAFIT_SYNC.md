# NovaFit profile synchronization 💙

NovaFit publishes machine-readable project facts from its `main` branch at:

```text
https://raw.githubusercontent.com/LiriothTeltanion/NovaFit/main/portfolio/project.json
```

The profile keeps a reviewed snapshot in
`data/project-snapshots/novafit.json`. The snapshot updates only the existing
NovaFit entry in `profile.json`; the profile builder then regenerates
`README.md` and `README_EXPANDED.md`.

## What updates automatically

- semantic version and active status;
- manifest-backed product summary;
- discovered automated-test count and theme count;
- public visual-asset count;
- canonical GitHub Pages demo URL;
- verified capabilities, one-click verification and release-audit commands.

Identity, contact information, other projects, skills, education, artwork and
localized profiles remain human-maintained. This boundary prevents one project
manifest from rewriting the rest of Kevin's public profile.

## Safe local refresh

After NovaFit's generated manifest is published, run:

```powershell
python scripts/sync_novafit.py --url https://raw.githubusercontent.com/LiriothTeltanion/NovaFit/main/portfolio/project.json --write
python scripts/sync_novafit.py --check
powershell -ExecutionPolicy Bypass -File tools/profile/verify-profile.ps1
python -m unittest discover -s tests -v
git diff --check
```

The URL is an exact allow-list, the response is capped at 512 KiB, and schema,
repository identity, branch, the exact Pages origin, static-site privacy
boundaries, bounds and plain-text fields are
validated before any file is changed. Writes use temporary files and atomic
replacement. A failed fetch or invalid manifest leaves the profile untouched.

## GitHub automation

`.github/workflows/sync-novafit.yml` runs daily at `04:17 UTC` and can also be
started manually from GitHub Actions. It uses only the repository-scoped
`GITHUB_TOKEN`, validates all generated outputs and tests, and commits exactly
four managed files when verified facts changed:

- `data/project-snapshots/novafit.json`
- `profile.json`
- `README.md`
- `README_EXPANDED.md`

No personal access token or cross-repository secret is required. If branch
protection blocks direct automation commits, the workflow fails visibly without
force-pushing; run the same local refresh and publish the reviewed diff.

## NovaFit publishing contract

NovaFit owns the upstream facts. Its release workflow should run
`python scripts/sync_docs.py --write` and verify
`python scripts/sync_docs.py --check` before pushing `main`. The profile's next
scheduled or manual refresh then consumes that public manifest. This keeps app
code, NovaFit documentation and the main GitHub profile connected without
duplicating private runtime data. The profile links the public installable
showcase while continuing to describe the Windows desktop application as the
local-first runtime; the site is explicitly forbidden from reading the desktop
database or publishing runtime records.
