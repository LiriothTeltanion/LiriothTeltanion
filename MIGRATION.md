# GitHub Profile 2.0 Release Guide 🧭

## Objective

Publish the generated recruiter-first Profile 2.0 command center while preserving multilingual summaries, verified project evidence, accessible motion and the KC × LT creative identity.

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
git switch -c codex/profile-v2-novafit-signature
py -3 tools/profile/generate_signature_assets.py --check
py -3 scripts/build_profile.py --mode compact --output README.md
py -3 scripts/build_profile.py --mode expanded --output README_EXPANDED.md
py -3 scripts/validate_profile.py --readme README.md --max-lines 300
powershell -ExecutionPolicy Bypass -File tools/profile/verify-profile.ps1
git diff -- README.md profile.json assets scripts
```

Recommended commit:

```text
feat(profile): release v2 NovaFit and signature edition
```

## Why this structure is stronger

1. Target role, location, stack and availability are immediate.
2. Projects use one consistent evidence format.
3. No arbitrary skill percentages.
4. Nova Music Lab remains the flagship visual journey, while NovaFit v4.2.0 adds a privacy-safe product tour, manifest-backed evidence and deterministic seeded-demo analytics.
5. Secondary content is collapsible.
6. Spanish and Hebrew remain available without tripling the main README.
7. `profile.json` reduces drift.
8. Validation catches missing assets, unsafe SVG animation placement, absent reduced-motion behavior, corrupt rasters, payload regressions, placeholders, duplicate sections and uncontrolled growth.

## Before publishing

- Confirm NovaFit v4.2.0, its 124-test count, 12 themes and 58-asset manifest remain synchronized.
- Confirm Nova Music Lab live URL.
- Validate all GIF/SVG assets, responsive fallbacks and reduced-motion behavior on GitHub.
- Confirm `profile_version`, release tag and changelog all agree on `2.0.0` / `v2.0.0`.
- Pin Nova Music Lab, NovaFit, Christopher Portfolio and Fullstack2026.
- Unpin the profile repository itself.
- Archive or privatize empty public repositories.
