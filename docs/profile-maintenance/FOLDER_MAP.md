# Folder map

```text
LiriothTeltanion/
├── .github/
│   └── workflows/
│       └── profile-validation.yml  # Automated profile checks
├── assets/                         # Public banners and visual assets
│   ├── projects/                   # Featured-project cards
│   └── visuals/                    # Profile section illustrations
├── docs/
│   └── profile-maintenance/
│       ├── FOLDER_MAP.md
│       ├── PUBLIC_METADATA.md
│       ├── ROADMAP.md
│       └── WORKFLOW.md
├── extras/
│   ├── OPTIONAL-DYNAMIC-VISUALS.md # Opt-in contribution-snake guide
│   └── snake.yml                   # Inactive workflow template
├── preview/                        # Tracked visual-review archive
├── prompts/
│   └── CODEX_PROFILE.md            # Reusable focused-edit prompt
├── scripts/
│   ├── build_profile.py            # Compact/expanded README generator
│   └── validate_profile.py         # Lightweight generated-profile checks
├── tests/
│   └── test_profile_tooling.py     # Generator/validator regressions
├── tools/
│   └── profile/
│       ├── backup-readme.ps1       # Local README snapshot
│       └── verify-profile.ps1      # Repository/profile validator
├── .gitattributes
├── .gitignore                      # Portable local-only exclusions
├── AGENTS.md                       # Persistent maintenance rules
├── README.md                       # Public GitHub profile
├── README_EXPANDED.md              # Generated expanded profile variant
├── PROFILE_ES.md                   # Spanish profile summary
├── PROFILE_HE.md                   # Hebrew profile summary
├── profile.json                    # Canonical generated-profile data
├── build_profile.bat               # Windows generation and verification
├── verify_profile.bat              # Windows verification launcher
└── SETUP.md                        # Setup and first-run guide
```

## Generated local content

`tools/profile/backup-readme.ps1` creates `.local-backups/` at the repository
root. That directory is intentionally absent from the tracked tree and is
ignored by the repository's `.gitignore`, so the behavior is portable to every
clone.

## Directory roles

- `assets/` contains files used by the public README. Treat filenames and case
  as public API because GitHub resolves the relative paths.
- `preview/` contains retained rendering proofs and historical visual snapshots.
  It is not a cache and is not automatically pruned.
- `extras/` contains optional material that has no effect on the public profile
  in its current location.
- `.github/workflows/profile-validation.yml` validates profile changes on
  GitHub, runs the Python tooling tests and checks generated-file drift; the
  local PowerShell validator remains the required pre-publish check.
