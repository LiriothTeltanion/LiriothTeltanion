# GitHub Profile 2.1 Definitive Package 🌍✨

This folder is a complete, generated replacement for the GitHub profile repository presentation.

## Included

- recruiter-first `README.md`, validated at no more than 300 lines;
- optional expanded README;
- Spanish and Hebrew summaries;
- canonical `profile.json`;
- Profile `2.1.0` release metadata and changelog;
- compact/expanded generator;
- validator;
- Windows build/verify launchers;
- responsive animated professional banner with mobile and reduced-motion variants;
- responsive animated portfolio command center without arbitrary progress bars;
- Nova Music Lab museum-journey spotlight;
- Ivrit Sheli 2.0 full-stack production-proof card, responsive desktop/mobile/
  Hebrew RTL captures and a reduced-motion-safe animated tour;
- verified Ivrit evidence: 109 backend + 17 frontend = 126 passing tests,
  GitHub OAuth with PKCE, PostgreSQL/RLS, Alembic, Docker and structured logs;
- animated project constellation;
- animated engineering orbit;
- responsive country-boundary atlas tracing San Cristóbal to Beersheba, with animated and reduced-motion variants;
- animated learning roadmap;
- responsive NovaFit motivation and trust-system diagrams with reduced-motion behavior;
- profile-independent Training Atlas and anonymized seeded-demo theme evidence;
- allow-listed NovaFit project-manifest synchronization with offline drift checks;
- reusable KC ✦ LT identity generated from eight pen strokes and one restrained
  glowing four-point star;
- upload-ready Ivrit project and social-preview art without an unverified live
  deployment URL;
- migration guide.

## Regenerate

```bash
python scripts/build_profile.py --mode compact --output README.md
python scripts/build_profile.py --mode expanded --output README_EXPANDED.md
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

Update `profile.json` rather than editing repeated claims in generated Markdown. Keep Ivrit's source link public, but add a live URL only after the deployed HTTPS service, health checks and GitHub OAuth callback are verified.
