# AGENTS.md — Kevin Cusnir GitHub Profile

## Repository purpose

This is the special public GitHub profile repository for:

- Name: Kevin Cusnir
- Creative identity: Lirioth Teltanion
- GitHub username: `LiriothTeltanion`
- Contact email: `kevincusnir@gmail.com`
- Birthplace: San Cristóbal, Venezuela
- Current location: Beersheba, Israel
- Target roles: Junior Full-Stack Developer and Frontend Developer

The root `README.md` is rendered publicly on Kevin's GitHub profile.

## Core rules

- Treat this repository as a professional public portfolio, not as a disposable experiment.
- Preserve the current identity, multilingual structure, featured projects, animations, statistics and visual assets unless the task explicitly changes them.
- Never replace the entire `README.md` when a targeted edit is sufficient.
- Never delete assets until every reference has been checked.
- Keep `Kevin Cusnir` and `Lirioth Teltanion` fully visible in the main banner.
- Keep the correct email: `kevincusnir@gmail.com`.
- Do not invent employment, education, metrics, certifications, users, stars or technical claims.
- Distinguish finished functionality from roadmap items.
- Prefer accessible HTML and Markdown: meaningful alt text, readable hierarchy, keyboard-friendly links and reduced-motion fallbacks.
- Keep paths relative when assets are stored in the repository.
- Check desktop and narrow/mobile rendering after large visual edits.
- Avoid unnecessary dependencies and externally hosted widgets that are unreliable.
- Do not expose secrets, tokens, private documents, medical information, financial information or `.env` values.

## Authority and release discipline

- A `read only` request forbids file writes, backups, generators in write mode,
  dependency installation, branch or configuration changes, staging, commits,
  pushes, tags, releases, deployments and public-account updates.
- `GO` authorizes complete implementation and validation of the already agreed
  scope. It does not broaden that scope or authorize commit, push, release,
  deployment or another external publication action.
- Treat every pre-existing worktree change as Kevin's work. Never stash, reset,
  clean, overwrite or discard it to make the repository easier to edit.
- Before repository-changing work, identify the current canonical profile
  version, choose the smallest justified Semantic Versioning increment and
  report the intended old → new version.
- Preview and beta tools are welcome in labeled, non-critical experiments with
  a rollback path. Public profile claims, links and releases must represent
  stable, verified evidence.
- Never move, delete or reuse a published tag. Correct release mistakes forward
  with a new patch version and tag the exact finalized release commit.
- Scheduled automation may detect and report project-fact drift, but it must not
  rewrite, commit or push public profile content without Kevin's review.

## Required workflow

Before editing:

1. Read the relevant README sections and asset files.
2. Check `git status`.
3. Identify the smallest coherent change.
4. Back up the README before a major restructure:
   `powershell -ExecutionPolicy Bypass -File tools/profile/backup-readme.ps1`

After editing:

1. Run:
   `powershell -ExecutionPolicy Bypass -File tools/profile/verify-profile.ps1`
2. Review `git diff -- README.md assets`.
3. Confirm links and local asset paths.
4. Report exactly what changed, what was tested and any unresolved limitation.
5. Do not commit or push unless Kevin explicitly requests it.

## Current design priorities

- The animated top banner must not clip Kevin's name or the Lirioth Teltanion alias.
- Visual sections should remain readable rather than becoming animation-heavy noise.
- Featured projects should emphasize verifiable engineering evidence.
- Nova Music Lab should remain the strongest featured product.
- The profile should help recruiters understand Kevin quickly.
- Spanish, English and Hebrew content should remain internally consistent.

## Useful project files

- Public profile: `README.md`
- Visual assets: `assets/`
- Maintenance workflow: `docs/profile-maintenance/WORKFLOW.md`
- Improvement roadmap: `docs/profile-maintenance/ROADMAP.md`
- Reusable Codex prompt: `prompts/CODEX_PROFILE.md`
- Validation: `tools/profile/verify-profile.ps1`
- Backup: `tools/profile/backup-readme.ps1`
