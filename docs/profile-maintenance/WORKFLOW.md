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

## Authority boundaries

- `read only` means zero writes: do not create backups, run generators in write
  mode, install dependencies, change branches/configuration/refs, stage, commit,
  push, tag, release, deploy or edit public account settings.
- `GO` authorizes complete implementation and validation of the scope already
  reviewed with Kevin. It does not authorize a broader redesign or any external
  publication action.
- Existing worktree changes belong to Kevin. Never stash, reset, clean,
  overwrite or discard them; work around them or stop and explain the overlap.
- Preview and beta tools may be used in clearly labeled non-critical contexts
  with rollback. Public links, screenshots, claims and releases must remain
  stable and verified.

NovaFit's version, verified capability and quality facts are synchronized from
its public project manifest. See [`NOVAFIT_SYNC.md`](./NOVAFIT_SYNC.md) before
changing the managed NovaFit fields by hand.

Ivrit Sheli's version, deployment, publication, test and boundary facts are also
manifest-backed. Read [`IVRIT_SHELI_SYNC.md`](./IVRIT_SHELI_SYNC.md) before
changing its managed fields. The current reviewed contract is source/live
2.2.0, 139 backend + 48 frontend = 187 tests, healthy Railway/PostgreSQL
readiness and matching public v2.2.0 Git tag and GitHub Release. The final live
OAuth code exchange, authenticated session refresh and logout remain unverified
E2E.

## Before a large change

Back up the README before a major restructure or wide visual rewrite:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\profile\backup-readme.ps1
```

The backup is placed in `.local-backups/` and ignored by Git. A focused metadata,
documentation or one-section edit does not require a new backup.

## Versioning and release integrity

Before implementation, read `profile.json`, classify the change and announce
the intended version:

- structural identity or presentation generation: increment `X.0.0`;
- contained feature, visual or functional expansion: increment `X.Y.0`;
- narrow correction without presentation expansion: increment `X.Y.Z`.

Set new work to `release-candidate` until publication is explicitly approved.
Never move, delete or reuse a published tag. If a tag or release contains stale
metadata, correct forward with a new patch version.

For a final release, first validate the `release-candidate`. After Kevin's
explicit publication approval, set the in-tree status to `released`, run the
deterministic build and data checks, commit that exact final state, create the
annotated tag at the same commit, and run the complete verifier again. Only then
push the commit and tag atomically, create the GitHub Release and verify the
public state. The verifier rejects `released` metadata when the matching tag is
absent, points elsewhere or contains non-final metadata. A local unpublished
tag may be removed if this pre-push gate fails; a published tag is immutable.

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

Confirm both checked-in project snapshots and generated README modes agree:

```powershell
python scripts/sync_ivrit_sheli.py --check
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

The KC ✦ LT brand system is generated from eight canonical pen strokes and one
separate four-point star. In Profile 2.2 the star is larger, sits lower like the
punctuation in `KC·LT` and uses a brighter blue glow. After changing its
geometry, palette or animation, regenerate and prove that the brand, banner and
social SVG embeddings agree:

```powershell
python tools/profile/generate_signature_assets.py
python tools/profile/generate_signature_assets.py --check
```

The star reveal runs once and must become static when reduced motion is
requested. The monochrome variant intentionally keeps the star without blur.

Ivrit's visual family was introduced in Profile 2.1. Profile 2.4 rebuilds the
tour from fresh live 2.2.0 desktop, 390-pixel mobile and Hebrew RTL captures.
They use Kevin's isolated account, may show only his already-public name/avatar
plus default recommendations, and must not contain private learning history:

```text
assets/ivrit-sheli-product-tour.gif
assets/ivrit-sheli-2-dashboard.png
assets/ivrit-sheli-2-mobile.png
assets/ivrit-sheli-2-hebrew-rtl.png
assets/projects/ivrit-sheli-logo.svg
assets/social/ivrit-sheli-social-preview.svg
assets/social/ivrit-sheli-social-preview.png
```

Keep desktop, narrow/mobile and Hebrew RTL frames readable; use PNG fallbacks
for reduced motion and optimize the GIF so the complete referenced README visual
payload remains below 8 MiB. The copied social SVG must point to
`../projects/ivrit-sheli-logo.svg` and embed the canonical compact KC ✦ LT pen
paths and star before running `generate_signature_assets.py --check`.

Do not publish a Railway or other live link until its HTTPS page, read-only demo,
`/health/ready`, `/version` and backing database have been tested. For the
current Ivrit 2.2.0 deployment, live/ready, dictionary and PostgreSQL checks are
verified at the manifest-recorded production commit. GitHub OAuth consent and
cancellation are verified. The final authorization-code exchange,
authenticated session refresh and logout remain pending and must not be
described as end-to-end verified. When deployment evidence changes, refresh the
strict manifest snapshot, canonical project data, both localized profiles and
public metadata in the same patch.

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
6. The previous and new profile version, or why no increment was needed.

## Publish with GitHub Desktop

Publishing happens only after Kevin explicitly approves it.

### Desktop review and final commit

1. Inspect every changed file.
2. Confirm that no secret or personal document is included.
3. Use a focused commit message, for example:
   - `fix: prevent profile banner text clipping`
   - `docs: refresh featured project evidence`
   - `design: improve mobile readability`
4. Confirm `profile.json` says `released`, regenerate both READMEs and run the
   deterministic data/build checks.
5. Commit the exact final state to `main` in GitHub Desktop.
6. Do **not** click **Push origin** yet. GitHub Desktop cannot guarantee the
   required atomic branch-plus-tag publication by itself.

### Approved terminal release handoff

Open PowerShell in this repository only after Kevin has approved publication.
These commands fetch public tags, reject reuse, create an annotated tag, run the
exact-tag verifier, push branch and tag atomically, and create a stable Release:

```powershell
$profile = Get-Content -Raw -LiteralPath .\profile.json | ConvertFrom-Json
$tag = [string]$profile.release.tag
$title = [string]$profile.release.title
if ($profile.release.status -ne 'released') { throw 'profile.json is not finalized.' }

git fetch origin --tags --prune
if ($LASTEXITCODE -ne 0) { throw 'Could not refresh public tags.' }
git show-ref --verify --quiet "refs/tags/$tag"
if ($LASTEXITCODE -eq 0) { throw "Tag $tag already exists; increment the patch version." }
if ($LASTEXITCODE -ne 1) { throw "Could not check tag $tag." }

$dirty = @(git status --porcelain=v1)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) { throw 'The repository is not clean.' }
$head = (git rev-parse HEAD).Trim()
git tag -a $tag $head -m $title
if ($LASTEXITCODE -ne 0) { throw "Could not create annotated tag $tag." }

powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\profile\verify-profile.ps1
if ($LASTEXITCODE -ne 0) { throw 'Release verification failed; do not push.' }
git push --atomic origin "HEAD:refs/heads/main" "refs/tags/$tag"
if ($LASTEXITCODE -ne 0) { throw 'Atomic branch and tag push failed.' }

gh release create $tag --verify-tag --title $title --generate-notes
if ($LASTEXITCODE -ne 0) { throw 'GitHub Release creation failed.' }
```

The tag-availability check is deliberately performed after `git fetch --tags`,
so an existing public version cannot be accidentally reused. If verification
fails before the push, the new tag is still local and unpublished; inspect the
failure before removing or recreating it. Never move or delete a published tag.

### Public verification

Run the following checks after publication:

```powershell
$remoteMain = ((git ls-remote origin refs/heads/main) -split '\s+')[0]
$peeled = @(git ls-remote origin "refs/tags/$tag^{}")
if ($peeled.Count -ne 1) { throw 'The annotated remote tag could not be peeled.' }
$remoteTagCommit = (($peeled[0] -split '\s+')[0]).Trim()
if ($remoteMain -ne $head -or $remoteTagCommit -ne $head) {
    throw 'Public main, the release tag and the finalized local commit differ.'
}

$release = gh release view $tag --json tagName,isDraft,isPrerelease,url | ConvertFrom-Json
if ($release.tagName -ne $tag -or $release.isDraft -or $release.isPrerelease) {
    throw 'The GitHub Release is missing or is not a stable published release.'
}
$release.url
```

Then:

1. Apply the separately approved About metadata, social previews and pin order.
2. Open the public profile in signed-in and signed-out views and inspect the
   rendered result at desktop and narrow/mobile widths.
3. Confirm the README marker, tag page and stable GitHub Release all show the
   same profile version.

## Recovery

When a change renders badly:

1. Do not create more edits immediately.
2. Compare the GitHub Desktop diff.
3. Restore from `.local-backups` or revert the commit.
4. Make a smaller change and validate again.

Never use destructive Git commands to discard an uncertain or mixed worktree.
