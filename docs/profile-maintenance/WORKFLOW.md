# Profile maintenance workflow

## One source of truth

Maintain one editable local clone of:

```text
https://github.com/LiriothTeltanion/LiriothTeltanion
```

Do not maintain a second editable copy elsewhere. Confirm the active repository
instead of relying on a machine-specific path:

```powershell
git rev-parse --show-toplevel
git remote get-url origin
```

## Start a session

1. Open the repository root.
2. Read `AGENTS.md`.
3. Check `git status --short --branch` before touching files.
4. Inspect the relevant README sections and referenced assets.
5. Define one concrete outcome and the smallest set of files it requires.
6. Preserve any pre-existing worktree changes that are outside that scope.

Do not pull, switch branches, commit or push merely to begin a maintenance
session. Those are separate actions that require an explicit reason and, for
publishing, Kevin's approval.

NovaFit's version, verified capability and quality facts are synchronized from
its public project manifest. See [`NOVAFIT_SYNC.md`](./NOVAFIT_SYNC.md) before
changing the managed NovaFit fields by hand.

## Before a large change

Back up the README before a major restructure or wide visual rewrite:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\profile\backup-readme.ps1
```

The backup is placed in `.local-backups/` and ignored by Git. A focused metadata,
documentation or one-section edit does not require a new backup.

## Editing guardrails

- Make targeted patches; do not replace the full README when a section edit is
  sufficient.
- Preserve Kevin Cusnir, Lirioth Teltanion, `kevincusnir@gmail.com`, project
  links, translations, animations and unrelated assets.
- Do not invent employment, education, certifications, users, stars, metrics or
  production-readiness claims.
- Keep local asset paths relative and case-correct.
- Check all references and `ASSET_MANIFEST.md` before renaming or deleting any
  asset. An unlinked file may still be retained provenance or preview history.
- Keep personal-looking wellness records and identity-linked private metrics out
  of public screenshots, GIFs and generated visuals.
- Distinguish verified functionality from planned work.
- Prefer accessible hierarchy, meaningful alt text, keyboard-friendly links and
  reduced-motion behavior.

## Validation

Run the repository validator from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\profile\verify-profile.ps1
```

For the complete local generation and QA pipeline on Windows, run
`build_profile.bat`. It regenerates both README modes, checks drift, validates
the localized profiles, compiles the tooling, runs doctests and unit tests, and
finishes with the PowerShell verifier.

Confirm the checked-in NovaFit snapshot and both generated README modes agree:

```powershell
python scripts/sync_novafit.py --check
```

Then inspect the patch itself:

```powershell
git diff --check
git status --short
git diff -- README.md assets
```

The validator checks identity, local references, CSS and SMIL animation
fallbacks, SVG accessibility, unsafe SVG transform composition, raster
decoding and the public visual payload budget. A successful script does not
replace human review: open changed text files, confirm every changed path
exists and ensure no private material or secret was added.

For a visual change, also render or open the affected section at desktop and
narrow/mobile widths. Confirm that names are not clipped, text remains readable,
links are usable and the reduced-motion experience is complete.

The global journey atlas is generated from pinned Natural Earth 1:110m public-
domain country data. Rebuild its desktop, mobile and reduced-motion variants
from the repository root with:

```powershell
python tools/profile/generate_world_globe.py
```

Once the pinned cache has been populated, prove that the committed globe assets
are reproducible without a network request or file write:

```powershell
python tools/profile/generate_world_globe.py --offline --check
```

The check must report `195/195 sovereign states represented`: 182 are supplied
by the two pinned Natural Earth layers and the 13 states omitted at 1:110m are
rendered as deterministic named centroid markers. Natural Earth may also show
territories or disputed entities; those extras do not change the 195-state
coverage contract. Six crowded eastern-Caribbean markers are separated by
deterministic callout offsets and leader lines; their true projected anchors
remain encoded in the SVG.

Audit live public URLs locally when changing links or before publishing:

```powershell
python scripts/check_external_links.py
```

The matching GitHub Actions workflow runs weekly and manually. It fails for
convincing permanent missing responses while reporting bot blocks, rate limits,
timeouts and server errors as warnings.

## Preview retention policy

`preview/` is a tracked archive of rendering proofs and historical visual
snapshots. Preserve every existing file during normal maintenance.

- Do not treat previews as temporary build output.
- Do not delete, rename, recompress or overwrite them as part of an unrelated
  cleanup.
- Add a clearly named proof only when it materially helps review a large visual
  change.
- Any future size-reduction task must be explicit, must audit all references and
  historical value, and must receive approval before an asset is removed.

This policy also applies when a preview is not currently linked from README.md.
The ignored `.nova-pack-backup/` path is an accidental local package snapshot,
not a preview archive, and must not be committed.

## Review the final scope

Before handoff, report:

1. Every changed or created file.
2. The exact behavior or documentation changed.
3. Commands and visual checks executed, including their result.
4. Any limitation that remains unresolved.
5. Confirmation that no commit or push was performed unless requested.

## Publish with GitHub Desktop

Publishing happens only after Kevin explicitly approves it.

1. Inspect every changed file.
2. Confirm that no secret or personal document is included.
3. Use a focused commit message, for example:
   - `fix: prevent profile banner text clipping`
   - `docs: refresh featured project evidence`
   - `design: improve mobile readability`
4. Commit to the current branch.
5. Push origin.
6. Open the public profile and inspect the rendered result.

## Recovery

When a change renders badly:

1. Do not create more edits immediately.
2. Compare the GitHub Desktop diff.
3. Restore from `.local-backups` or revert the commit.
4. Make a smaller change and validate again.

Never use destructive Git commands to discard an uncertain or mixed worktree.
