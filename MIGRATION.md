# GitHub Profile 2.3 Release-Candidate Guide 🧭

## Objective

Prepare **Profile 2.3 — Verified Ivrit Synchronization Edition** without changing
the established visual identity. Nova Music Lab remains first; Ivrit Sheli 2.2.0
remains second with manifest-backed 187-test, Railway and PostgreSQL evidence,
strict multilingual parity and honest publication, OAuth and media boundaries.
Tagging, releasing and merging remain separate approved actions.

## Copy scope

Copy the full contents of this folder into `LiriothTeltanion/LiriothTeltanion`, excluding package-only notes only when preferred.

Core runtime files:

```text
README.md
README_EXPANDED.md
PROFILE_ES.md
PROFILE_HE.md
profile.json
CHANGELOG.md
assets/
scripts/build_profile.py
scripts/validate_profile.py
scripts/sync_ivrit_sheli.py
data/project-snapshots/ivrit-sheli.json
.github/workflows/sync-ivrit-sheli.yml
docs/profile-maintenance/IVRIT_SHELI_SYNC.md
tools/profile/generate_signature_assets.py
build_profile.bat
verify_profile.bat
.gitattributes
```

## Workflow

```powershell
git status --short
git switch -c codex/profile-v2.3-ivrit-sync
py -3 scripts/sync_ivrit_sheli.py --check
py -3 scripts/sync_novafit.py --check
py -3 tools/profile/generate_signature_assets.py --check
py -3 scripts/build_profile.py --mode compact --output README.md --check
py -3 scripts/build_profile.py --mode expanded --output README_EXPANDED.md --check
py -3 scripts/validate_profile.py --readme README.md --max-lines 300 --mode compact --check-localized
py -3 scripts/validate_profile.py --readme README_EXPANDED.md --max-lines 300 --mode expanded
py -3 -m unittest discover -s tests -v
powershell -ExecutionPolicy Bypass -File tools/profile/verify-profile.ps1
git diff --check
git diff -- README.md README_EXPANDED.md PROFILE_ES.md PROFILE_HE.md profile.json scripts tests docs .github
```

Recommended commit:

```text
feat(profile): synchronize verified Ivrit 2.2 evidence
```

## Why this structure is stronger

1. Target role, location, stack and availability are immediate.
2. Projects use one consistent evidence format.
3. Nova Music Lab remains the live visual and data flagship.
4. The KC ✦ LT visual system remains stable and recognizable across banners,
   social art and compact use.
5. Ivrit Sheli adds verifiable full-stack depth: React 19, TypeScript, FastAPI,
   PostgreSQL 17, Alembic, GitHub OAuth with PKCE, tenant RLS, Docker,
   structured JSON logging and 187 passing tests.
6. Ivrit links directly to its verified Railway service. HTTPS,
   readiness/version, PostgreSQL and the read-only demo passed public QA;
   OAuth consent and cancellation passed, while the final code exchange,
   authenticated session refresh and logout remain visibly pending.
7. NovaFit v4.2.0 retains its privacy-safe product tour, manifest-backed evidence
   and deterministic seeded-demo analytics.
8. No arbitrary skill percentages are used, and secondary content remains
   collapsible.
9. Spanish and Hebrew remain available without tripling the main README.
10. Strict Ivrit and NovaFit manifests reduce repeated project-fact drift.
11. Spanish and Hebrew include machine-checked canonical version, test,
    readiness, OAuth and media facts while retaining human-written prose.
12. Validation catches missing assets, unsafe SVG animation placement, absent
    reduced-motion behavior, corrupt rasters, payload regressions, placeholders,
    duplicate sections and uncontrolled growth.

## Before publishing

- Confirm Nova Music Lab remains first and its live URL still works.
- Confirm Ivrit Sheli 2.2.0 remains second, its source and live demo are public,
  and its verified test arithmetic is 139 backend + 48 frontend = 187 total.
- Recheck `https://ivritsheli-production.up.railway.app`, `/health/live`,
  `/health/ready` and `/version`; confirm PostgreSQL and dictionary readiness.
- Keep the OAuth limitation explicit: consent and cancellation are verified,
  but final code exchange, session refresh and logout remain pending E2E.
- Confirm the Ivrit deployment, Git tag and GitHub Release all agree on v2.2.0;
  keep that product release separate from the published Profile v2.3.0 release.
- Keep Ivrit GIF/PNG interface media labeled as archived 2.1.x evidence until
  fresh desktop/mobile/RTL 2.2 captures pass visual QA.
- Confirm NovaFit v4.2.0, its 124-test count, 12 themes and 58-asset manifest
  remain synchronized.
- Validate all GIF/SVG/PNG assets, responsive fallbacks and reduced-motion
  behavior on desktop, narrow/mobile and GitHub-rendered views.
- Confirm `profile_version`, released tag metadata, changelog and GitHub Release
  all agree on `2.3.0` / `v2.3.0`.
- Pin Nova Music Lab, Ivrit Sheli, NovaFit, Christopher Portfolio and CV in that
  order. Keep Fullstack2026 public as learning evidence but outside the pins.
- Unpin the profile repository itself.
- Keep the profile website pointed to the verified Nova Music Lab deployment.
- Archive or privatize empty public repositories.
