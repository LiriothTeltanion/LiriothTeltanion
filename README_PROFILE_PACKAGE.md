# GitHub Profile Definitive Package 🌍✨

This folder is a complete, generated replacement for the GitHub profile repository presentation.

## Included

- recruiter-first `README.md` — 262 lines;
- optional expanded README;
- Spanish and Hebrew summaries;
- canonical `profile.json`;
- compact/expanded generator;
- validator;
- Windows build/verify launchers;
- animated professional banner;
- animated portfolio command center;
- animated project constellation;
- animated engineering orbit;
- detailed Beersheba-centered globe plus static fallback;
- animated learning roadmap;
- NovaFit 4.0 analytics tour GIF;
- actual NovaFit GUI capture;
- migration guide.

## Regenerate

```bash
python scripts/build_profile.py --mode compact --output README.md
python scripts/build_profile.py --mode expanded --output README_EXPANDED.md
python scripts/validate_profile.py --readme README.md --max-lines 300
```

On Windows:

```text
build_profile.bat
verify_profile.bat
```

## Public recommendation

Use compact mode for the public profile. It keeps the deeper engineering approach, education and creative identity in `<details>` blocks while preserving a fast recruiter path.

Update `profile.json` rather than editing repeated claims in several Markdown locations.
