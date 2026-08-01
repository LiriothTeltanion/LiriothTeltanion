# Ivrit Sheli portfolio synchronization

Ivrit Sheli's recruiter-facing facts are synchronized from one strict public
manifest instead of being repeated manually across the generated profile.

## Authority and reviewed fallback

- Canonical upstream URL:
  `https://raw.githubusercontent.com/LiriothTeltanion/IvritSheli/main/portfolio/project.json`
- Required schema: `ivrit-sheli-portfolio-project-v2`
- Reviewed local snapshot: `data/project-snapshots/ivrit-sheli.json`
- Synchronizer: `scripts/sync_ivrit_sheli.py`
- Scheduled/manual read-only audit: `.github/workflows/sync-ivrit-sheli.yml`

The URL is an exact allow-list, not a user-selectable remote. Downloads are
bounded to 512 KiB, require UTF-8 JSON and reject missing or extra fields,
identity drift, unsafe Markdown, inconsistent test arithmetic, unready live
dependencies and optimistic OAuth or visual claims. The v2 contract also keeps
the release implementation commit separate from the later runtime commit that
may serve the same public version.

After the exact URL passes the allow-list, network reads add an internal
timestamp-only cache key plus no-cache headers. This prevents an older GitHub
raw-CDN edge response from regressing newer reviewed release evidence; callers
still cannot supply another host, path or query string.

The local snapshot is the reviewed offline source of truth. A `404` in the
GitHub workflow produces a warning and runs the complete offline drift check;
other network errors and every invalid manifest fail closed. When the upstream
manifest exists, the workflow compares it against the reviewed snapshot and
fails on drift without writing, committing or pushing. The fallback never turns
invalid remote data into an accepted update. A same-version remote payload also
cannot regress the reviewed `2.4.0-live-and-published` state while an upstream
publication-sync change is propagating.
The reviewed snapshot also rejects a different release implementation commit
under the same Ivrit semantic version. That situation requires an explicit
evidence review or a new Ivrit version; scheduled automation cannot silently
redefine which implementation baseline the release proof belongs to.

## Current verified contract

| Evidence | Reviewed value |
| --- | --- |
| Source and live version | `2.4.0` |
| Tests | 151 backend + 62 frontend = 213 unique tests |
| Live service | Railway production at `https://ivritsheli-production.up.railway.app` |
| Release implementation baseline | `03bf84b9268ff8be528c0fab3c670f9652ee23b0` |
| Readiness | live, ready, PostgreSQL and 48-entry dictionary checks true on 2026-07-21 |
| Publication | deployment, Git tag and GitHub Release all `v2.4.0` |
| OAuth | Identity-only Google sign-in, reload persistence, session refresh, logout and signed-out reload verified; live GitHub session and re-login after logout remain unverified |
| Profile-owned interface media | archived `2.2.0`; it is not visual proof of the live `2.4.0` interface |
| Upstream manifest visual state | English entry/read-only tour browser path verified; README screenshots remain `2.1.x` and social preview remains `2.2.0` |

## Managed outputs

The synchronizer copies the existing profile object and may change only the
canonical Ivrit Sheli project plus these deterministic generated outputs:

- `data/project-snapshots/ivrit-sheli.json`;
- `profile.json`;
- `README.md`;
- `README_EXPANDED.md`.

It does not rewrite Kevin's identity, Nova Music Lab, NovaFit, localized prose,
assets, repository settings, tags, releases or deployment configuration.
When profile-owned media has already passed current-version browser QA, a
same-version upstream manifest with older visual metadata cannot downgrade that
local evidence. The advance to `2.4.0` deliberately expires the existing
`2.2.0` captures until a matching desktop/mobile/RTL set is reviewed.
Spanish and Hebrew remain human-written, then the localized validator checks
their canonical fact marker and visible Ivrit version/test/deployment tokens.

## Local commands

Verify the reviewed snapshot and all generated outputs without network access:

```powershell
python scripts/sync_ivrit_sheli.py --check
```

Refresh from the exact upstream URL only after it exists:

```powershell
python scripts/sync_ivrit_sheli.py `
  --url https://raw.githubusercontent.com/LiriothTeltanion/IvritSheli/main/portfolio/project.json `
  --write
```

Then run both project drift checks and the full profile validation:

```powershell
python scripts/sync_ivrit_sheli.py --check
python scripts/sync_novafit.py --check
python scripts/validate_profile.py --readme README.md --max-lines 300 --mode compact --check-localized
python -m unittest discover -s tests -v
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/profile/verify-profile.ps1
git diff --check
```

## Change discipline

1. Update the Ivrit repository's manifest from verified source, deployment and
   test evidence.
2. Run the remote synchronization command here.
3. Review the exact snapshot and `profile.json` diff before trusting generated
   prose.
4. Update Spanish, Hebrew and public metadata in the same profile release.
5. Keep screenshots and GIFs on their real capture version and mark them
   archived until a fresh `2.4.0` desktop/mobile/RTL capture set has been
   inspected.
6. Verify Git tags and GitHub Releases independently; never infer them or OAuth
   completion from a healthy Railway deployment.

The Ivrit and NovaFit workflows share one concurrency group so their read-only
remote drift audits do not compete for the same generated-profile validation.
Every actual synchronization remains a local, reviewed and versioned change.
