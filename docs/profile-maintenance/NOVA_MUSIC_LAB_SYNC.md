# Nova Music Lab profile release sync 🎧

Nova Music Lab owns the release evidence used to refresh the GitHub profile. Its
canonical public manifest is:

```text
https://liriothteltanion.github.io/NovaMusicLab/release-profile-manifest.json
```

This GitHub Pages artifact is the deployment attestation. The similarly named
file tracked in Nova Music Lab's `main` branch may deliberately remain a
`private-candidate`; it is source material, not proof that Pages serves that
release. The sync sends `Cache-Control: no-cache`, `Pragma: no-cache` and a
unique query value so a stale CDN response cannot silently certify a release.

The profile-side tool is intentionally review-gated. Running it without a mode
performs a read-only audit. `--write` does **not** edit `profile.json`,
`README.md`, `README_EXPANDED.md` or `assets/`; it prepares a checksum-verified
candidate under the ignored `.cache/nova-music-lab-profile-candidates/`
directory.

This kept **Profile 2.4.0 — released 2026-07-18** unchanged while its candidate
was reviewed, and **Profile 2.5.0 — released 2026-08-01** promoted the first
deployed-manifest evidence package. **Profile 2.6.0 — released 2026-08-09** was
promoted only after its own complete profile gate. The currently
accepted upstream evidence is **Nova Music Lab 1.6.0 — deployed 2026-08-09**.
A tracked private-candidate manifest is never acceptable profile evidence, even
when its version matches the public app.

## Upstream contract

`public/release-profile-manifest.json` uses schema
`nova-music-profile-release-v1` and must declare:

- the exact Nova Music Lab repository, `main` branch and GitHub Pages URL;
- `release.status`: `private-candidate` or `deployed`;
- a strict semantic version;
- a full 40-character source commit for deployed releases;
- real ISO calendar dates for capture and deployment, with `deployed_on`
  required for deployment;
- every media file's repository-relative path, SHA-256, byte count, pixel size,
  language, theme and viewport.

Every deployed version must include these stable media identities:

| ID | Purpose | Rule |
|---|---|---|
| `profile-hero-desktop` | wide GitHub profile/README proof | static PNG or JPEG |
| `profile-hero-mobile` | narrow/mobile proof | static PNG or JPEG |
| `profile-tour` | concise interaction tour | GIF |
| `profile-tour-static` | reduced-motion tour fallback | static PNG or JPEG |
| `social-preview` | repository/profile share card | 1280 × 640 PNG |

Source paths must remain under `assets/releases/v<version>/`. After the live
Pages manifest declares a deployed full commit, each media file is read from
that immutable commit on `raw.githubusercontent.com`, not from Pages or a
mutable branch. The tool also reads `package.json` from the same commit and
requires its version to match the manifest. The required README-facing media
must remain within the existing 8 MiB referenced-visual budget.

A private candidate may temporarily use a null commit while being checked from
a local Nova Music Lab worktree. That state can never be staged or accepted as
public profile evidence.

## Read-only audit

After Nova Music Lab publishes a deployed manifest:

```powershell
python scripts/sync_nova_music_lab.py
```

The command:

1. fetches only the exact allow-listed GitHub Pages manifest with cache bypass;
2. requires a deployed status and validates project identity, version, commit
   and real calendar dates;
3. reads `package.json` and media from the declared commit on raw GitHub;
4. verifies bytes, SHA-256 and image dimensions;
5. compares the upstream manifest with the reviewed profile snapshot;
6. checks that profile-owned media and `portfolio_sync` still match.

It returns a non-zero status on drift and never writes a file.

To review a local Nova Music Lab checkout before deployment:

```powershell
python scripts/sync_nova_music_lab.py `
  --manifest C:\path\to\NovaMusicLab\public\release-profile-manifest.json `
  --source-root C:\path\to\NovaMusicLab
```

## Explicit local candidate

Only after the manifest says `deployed`, includes a full commit and records
`deployed_on`, switch the profile repository to a dedicated review branch and
run:

```powershell
python scripts/sync_nova_music_lab.py --write
```

The tool refuses `main`, `master`, `trunk`, a detached branch, a private
candidate, a missing commit, stale package version, mismatched media or an
attempt to replace a different candidate at the same content-addressed path.
Successful output contains:

- the normalized source manifest;
- all verified media, named by stable ID;
- `candidate-plan.json`, including intended profile targets and the exact
  `portfolio_sync` evidence record;
- an explicit reminder that publication is not authorized.

Because `.cache/` is ignored, staging cannot silently become a public profile
change. Copying candidate files into `assets/`, accepting the reviewed snapshot,
updating `profile.json`, regenerating the READMEs and selecting a new profile
version remain deliberate human-reviewed steps.

## Promotion checklist

For every future deployed Nova Music Lab version:

1. Run the read-only audit and then stage the candidate on a non-main branch.
2. Open desktop, mobile and GIF assets; check legibility, motion, privacy and
   truthful version labels.
3. Provide a static reduced-motion route in the generated profile.
4. Copy approved media to the candidate plan's exact profile targets.
5. Copy the normalized manifest to
   `data/project-snapshots/nova-music-lab.json`.
6. Add the candidate plan's `portfolio_sync` record to the canonical Nova Music
   Lab project in `profile.json`; update only reviewed, source-backed claims.
7. Choose the smallest justified new profile version and keep it
   `release-candidate` until Kevin explicitly approves publication.
8. Regenerate both README modes, run the full profile verifier and inspect the
   desktop, mobile and reduced-motion result.
9. Commit, push, tag and publish only through the separately approved profile
   release workflow.

`.github/workflows/sync-nova-music-lab.yml` exposes the same audit as an explicit
manual GitHub Action with `contents: read`, disabled credential persistence and
a final clean-diff assertion. The live v1.6.0 deployment now makes a future
scheduled read-only drift audit possible, but scheduling remains a separate
reviewed decision; the workflow must never rewrite, commit, push or auto-merge
profile content.
