# GitHub Profile 2.1 Release Guide 🧭

## Objective

Publish the generated recruiter-first Profile 2.1 command center while preserving multilingual summaries, verified project evidence, accessible motion and the KC ✦ LT creative identity. Nova Music Lab remains the first flagship; Ivrit Sheli 2.0 becomes the second project as public, deployment-ready full-stack proof without claiming an unverified live URL.

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
tools/profile/generate_signature_assets.py
build_profile.bat
verify_profile.bat
.gitattributes
```

## Workflow

```powershell
git status --short
git switch -c codex/profile-v2.1-fullstack-star
py -3 tools/profile/generate_signature_assets.py --check
py -3 scripts/build_profile.py --mode compact --output README.md
py -3 scripts/build_profile.py --mode expanded --output README_EXPANDED.md
py -3 scripts/validate_profile.py --readme README.md --max-lines 300 --mode compact --check-localized
py -3 scripts/validate_profile.py --readme README_EXPANDED.md --max-lines 300 --mode expanded
powershell -ExecutionPolicy Bypass -File tools/profile/verify-profile.ps1
git diff -- README.md profile.json assets scripts
```

Recommended commit:

```text
feat(profile): release v2.1 full-stack proof and star signature
```

## Why this structure is stronger

1. Target role, location, stack and availability are immediate.
2. Projects use one consistent evidence format.
3. Nova Music Lab remains the live visual and data flagship.
4. Ivrit Sheli adds verifiable full-stack depth: React 19, TypeScript, FastAPI,
   PostgreSQL 17, Alembic, GitHub OAuth with PKCE, tenant RLS, Docker,
   structured JSON logging and 126 passing tests.
5. Ivrit source and deployment readiness remain separate from live deployment;
   no website is linked until the real HTTPS service and OAuth flow pass QA.
6. NovaFit v4.2.0 retains its privacy-safe product tour, manifest-backed evidence
   and deterministic seeded-demo analytics.
7. No arbitrary skill percentages are used, and secondary content remains
   collapsible.
8. Spanish and Hebrew remain available without tripling the main README.
9. `profile.json` reduces drift.
10. Validation catches missing assets, unsafe SVG animation placement, absent
    reduced-motion behavior, corrupt rasters, payload regressions, placeholders,
    duplicate sections and uncontrolled growth.

## Before publishing

- Confirm Nova Music Lab remains first and its live URL still works.
- Confirm Ivrit Sheli remains second, its source is public, and its verified test
  arithmetic is 109 backend + 17 frontend = 126 total.
- Keep the Ivrit live URL absent while deployment is pending. Add it only after
  HTTPS, `/health/ready`, `/version` and the GitHub OAuth callback work publicly.
- Confirm NovaFit v4.2.0, its 124-test count, 12 themes and 58-asset manifest
  remain synchronized.
- Validate all GIF/SVG/PNG assets, responsive fallbacks and reduced-motion
  behavior on desktop, narrow/mobile and GitHub-rendered views.
- Confirm `profile_version`, release tag and changelog all agree on `2.1.0` /
  `v2.1.0`.
- Pin Nova Music Lab, Ivrit Sheli, NovaFit and Christopher Portfolio in that
  order. Keep Fullstack2026 public as learning evidence but outside the top four.
- Unpin the profile repository itself.
- Keep the profile website pointed to the verified Nova Music Lab deployment.
- Archive or privatize empty public repositories.
