# Profile maintenance workflow

## One source of truth

The working repository must be:

```text
Desktop\Dev\00_GitHub_Profile\LiriothTeltanion
```

Do not maintain a second editable copy elsewhere. GitHub is the remote source; this folder is the local working copy.

## Start a session

1. Run `START_PROFILE_WORK.cmd` from the parent folder.
2. Confirm the repository is synchronized.
3. Open only the repository folder in ChatGPT/Codex.
4. Read `AGENTS.md`.
5. Define one concrete outcome.

## Before a large change

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\profile\backup-readme.ps1
```

## Validation

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\profile\verify-profile.ps1
```

The validator checks the repository, README, expected identity information and local asset references.

## Publish with GitHub Desktop

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
