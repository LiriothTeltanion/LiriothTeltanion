# Profile 2.3 — Verified Ivrit Synchronization Edition 🌍✨

This folder is a complete, generated replacement for the GitHub profile repository presentation.

## Included

- recruiter-first `README.md`, validated at no more than 300 lines;
- optional expanded README;
- Spanish and Hebrew summaries;
- canonical `profile.json`;
- Profile `2.3.0` release-candidate metadata and changelog;
- compact/expanded generator;
- validator;
- Windows build/verify launchers;
- responsive animated professional banner with mobile and reduced-motion variants;
- responsive animated portfolio command center without arbitrary progress bars;
- Nova Music Lab museum-journey spotlight;
- Ivrit Sheli 2.2.0 live full-stack product card plus honestly labeled archived
  2.1.x desktop/mobile/Hebrew RTL captures and reduced-motion-safe tour;
- verified Ivrit evidence: 139 backend + 48 frontend = 187 passing tests,
  GitHub OAuth with PKCE, PostgreSQL/RLS, Alembic, Docker and structured logs;
- verified Railway production, live/ready and PostgreSQL/dictionary readiness at
  the recorded production commit;
- verified GitHub OAuth consent and cancellation, with the final
  authorization-code exchange, session refresh and logout retained as clear
  pending E2E limitations;
- animated project constellation;
- animated engineering orbit;
- responsive country-boundary atlas tracing San Cristóbal to Beersheba, with animated and reduced-motion variants;
- animated learning roadmap;
- responsive NovaFit motivation and trust-system diagrams with reduced-motion behavior;
- profile-independent Training Atlas and anonymized seeded-demo theme evidence;
- allow-listed NovaFit project-manifest synchronization with offline drift checks;
- strict allow-listed Ivrit project-manifest synchronization with a reviewed
  offline snapshot, semantic parity checks and safe 404 workflow fallback;
- reusable KC ✦ LT identity generated from eight pen strokes and one larger,
  lowered four-point star with a brighter blue glow;
- retained Ivrit project/social-preview provenance, explicitly marked as
  pre-2.2 until a synchronized 2.2 SVG/PNG pair passes fresh visual QA;
- migration guide.

## Regenerate

```bash
python scripts/build_profile.py --mode compact --output README.md
python scripts/build_profile.py --mode expanded --output README_EXPANDED.md
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

Update `profile.json` through the strict project synchronizers rather than editing repeated claims in generated Markdown. Keep both Ivrit's public source and verified Railway demo visible. Do not describe OAuth as end-to-end verified until the final authorization-code exchange, authenticated session refresh and logout pass; consent and cancellation are the completed checks in this candidate. Ivrit's deployment, Git tag and GitHub Release now agree on 2.2.0, while archived README media remains separately labeled 2.1.x.
