# GitHub Profile Definitive Migration Guide 🧭

## Objective

Replace the repetitive profile with a generated recruiter-first command center while preserving multilingual summaries and creative identity.

## Copy scope

Copy the full contents of this folder into `LiriothTeltanion/LiriothTeltanion`, excluding package-only notes only when preferred.

Core runtime files:

```text
README.md
README_EXPANDED.md
PROFILE_ES.md
PROFILE_HE.md
profile.json
assets/
scripts/build_profile.py
scripts/validate_profile.py
build_profile.bat
verify_profile.bat
.gitattributes
```

## Workflow

```powershell
git status --short
git switch -c docs/definitive-recruiter-profile
py -3 scripts/build_profile.py --mode compact --output README.md
py -3 scripts/validate_profile.py --readme README.md --max-lines 300
git diff -- README.md profile.json assets scripts
```

Recommended commit:

```text
docs(profile): add definitive recruiter-first portfolio command center
```

## Why this structure is stronger

1. Target role, location, stack and availability are immediate.
2. Projects use one consistent evidence format.
3. No arbitrary skill percentages.
4. NovaFit 4.0 is shown through actual analytics and GUI evidence.
5. Secondary content is collapsible.
6. Spanish and Hebrew remain available without tripling the main README.
7. `profile.json` reduces drift.
8. The validator catches missing assets, placeholders, duplicate sections and uncontrolled growth.

## Before publishing

- Release NovaFit 4.0 first.
- Confirm Nova Music Lab live URL.
- Validate all GIF/SVG assets on GitHub.
- Pin Nova Music Lab, NovaFit, Christopher Portfolio and Fullstack2026.
- Unpin the profile repository itself.
- Archive or privatize empty public repositories.
