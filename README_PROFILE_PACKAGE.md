# Profile 2.5.0 — Living Flagship Evidence Edition 🌍✨

This folder is a complete, generated replacement for the GitHub profile repository presentation.

## Included

- recruiter-first `README.md`, validated at no more than 300 lines;
- optional expanded README;
- Spanish and Hebrew summaries;
- canonical `profile.json`;
- Profile `2.5.0` released metadata and changelog;
- compact/expanded generator;
- validator;
- Windows build/verify launchers;
- responsive animated professional banner with mobile and reduced-motion variants;
- responsive animated portfolio command center without arbitrary progress bars;
- Nova Music Lab 1.5.0 Living Artist Atlas spotlight with manifest-pinned
  desktop/mobile media, animated tour and static reduced-motion fallback;
- Ivrit Sheli 2.4.0 live full-stack product card plus honestly archived 2.2.0
  desktop/mobile/Hebrew RTL captures and a reduced-motion-safe tour;
- verified Ivrit evidence: 151 backend + 62 frontend = 213 passing tests,
  Google sign-in, PostgreSQL/RLS, Alembic, Docker and structured logs;
- verified Railway production, live/ready and PostgreSQL/dictionary readiness at
  the recorded production commit;
- verified Google identity sign-in, session refresh, onboarding persistence and
  logout, with live GitHub session and re-login retained as clear E2E limits;
- animated project constellation;
- animated engineering orbit;
- responsive country-boundary atlas tracing San Cristóbal to Beersheba, with animated and reduced-motion variants;
- animated learning roadmap;
- responsive NovaFit motivation and trust-system diagrams with reduced-motion behavior;
- profile-independent Training Atlas and anonymized seeded-demo theme evidence;
- allow-listed NovaFit project-manifest synchronization with offline drift checks;
- strict allow-listed Ivrit project-manifest synchronization with a reviewed
  offline snapshot, semantic parity checks and safe read-only drift auditing;
- strict deployed-manifest synchronization for Nova Music Lab, including exact
  commit, media hash, dimensions, cache bypass and review-candidate staging;
- review-gated scheduled automation that cannot commit or push to public
  `main`;
- exact release-tag integrity checks and forward-only patch repair discipline;
- reusable KC ✦ LT identity generated from eight pen strokes and one larger,
  lowered four-point star with a brighter blue glow;
- refreshed Nova Music Lab 1.5.0 social preview from its audited release bundle;
- migration guide.
- retained Profile 2.4 visual before/after and readiness report at
  `docs/profile-maintenance/PROFILE_2_4_0_VISUAL_REPORT.md`.

## Regenerate

```bash
python scripts/build_profile.py --mode compact --output README.md
python scripts/build_profile.py --mode expanded --output README_EXPANDED.md
python scripts/sync_nova_music_lab.py --check
python scripts/sync_ivrit_sheli.py --check
python scripts/sync_novafit.py --check
python tools/profile/generate_signature_assets.py --check
python scripts/validate_profile.py --readme README.md --max-lines 300 --mode compact --check-localized
python scripts/validate_profile.py --readme README_EXPANDED.md --max-lines 300 --mode expanded
powershell -ExecutionPolicy Bypass -File tools/profile/verify-profile.ps1
```

On Windows:

```text
build_profile.bat
verify_profile.bat
```

## Public recommendation

Use compact mode for the public profile. It keeps the deeper engineering approach, education and creative identity in `<details>` blocks while preserving a fast recruiter path led by Nova Music Lab and Ivrit Sheli.

Update `profile.json` through the strict project synchronizers rather than editing repeated claims in generated Markdown. Nova Music Lab's deployed Pages manifest is the authority for its 1.5.0 version, commit and release media; the tracked upstream candidate manifest is not public-deployment evidence. Keep both Ivrit's public source and verified Railway demo visible. Ivrit's deployment, Git tag and GitHub Release agree on 2.4.0, while the profile-owned 2.2.0 captures remain an explicitly archived visual record. Do not broaden the verified OAuth boundary beyond the production checks recorded in `profile.json`.
