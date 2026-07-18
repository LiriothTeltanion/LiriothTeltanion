# NovaFit profile synchronization 💙

NovaFit publishes machine-readable project facts from its `main` branch at:

```text
https://raw.githubusercontent.com/LiriothTeltanion/NovaFit/main/portfolio/project.json
```

The profile keeps a reviewed snapshot in
`data/project-snapshots/novafit.json`. The snapshot updates only the existing
NovaFit entry in `profile.json`; the profile builder then regenerates
`README.md` and `README_EXPANDED.md`.

## What the drift audit covers

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

## GitHub drift detection

`.github/workflows/sync-novafit.yml` runs daily at `04:17 UTC` and can also be
started manually from GitHub Actions. It has read-only repository permission,
fetches the exact allow-listed manifest and fails visibly when the reviewed
snapshot or generated outputs are stale. It never rewrites, commits or pushes
profile files.

After drift is reported, Kevin reviews and runs the local refresh. An approved,
versioned branch may then update exactly four managed files:

- `data/project-snapshots/novafit.json`
- `profile.json`
- `README.md`
- `README_EXPANDED.md`

No personal access token or cross-repository secret is required. Publication
remains a separate reviewed action; the scheduled audit cannot change `main` or
silently publish new project claims under an existing profile version.

NovaFit and Ivrit Sheli use the shared
`profile-project-sync-${{ github.repository }}` concurrency group. This prevents
their remote manifest audits from competing for the same generated-profile
validation run.

## NovaFit publishing contract

NovaFit owns the upstream facts. Its release workflow should run
`python scripts/sync_docs.py --write` and verify
`python scripts/sync_docs.py --check` before pushing `main`. The profile's next
scheduled or manual audit then detects whether the reviewed snapshot differs.
Kevin applies the local refresh only inside an approved versioned change. This keeps app
code, NovaFit documentation and the main GitHub profile connected without
duplicating private runtime data. The profile links the public installable
showcase while continuing to describe the Windows desktop application as the
local-first runtime; the site is explicitly forbidden from reading the desktop
database or publishing runtime records.
