# Optional dynamic contribution animation

The main README intentionally uses only local, stable artwork. This avoids broken
images when a third-party statistics service is unavailable.

A contribution snake workflow is included as an optional enhancement:

```text
extras/snake.yml
```

GitHub ignores workflow files under `extras/`, so the template is inactive by
default. Enabling it adds a scheduled third-party Action and an `output` branch;
it is not required for the profile.

## Security design

The template:

- starts with no default `GITHUB_TOKEN` permissions;
- gives the generation job read-only repository access;
- gives only the publishing job `contents: write` access;
- passes the token only to steps that require it;
- pins every external Action to an immutable full commit SHA; and
- prevents overlapping scheduled and manual runs.

The version comments are for maintainers; the SHA is the value GitHub executes.
The current pins were verified against the official upstream Git tag refs. When
upgrading, verify a new release in the Action's official repository and update
the full SHA and version comment together. Never replace a SHA with a floating
branch such as `main`.

## Enable it

1. Create `.github/workflows/` in your profile repository.
2. Copy the template so the reviewed source remains available:

   ```powershell
   Copy-Item .\extras\snake.yml .\.github\workflows\snake.yml
   ```

3. Review the copied workflow and its permissions.
4. Commit and push only the approved workflow change.
5. Open **Actions → Generate contribution snake → Run workflow**.
6. Confirm that both SVGs exist on the generated `output` branch.
7. Add the following section only after the first successful run:

```html
## 🐍 Contribution activity

<div align="center">
  <picture>
    <source
      media="(prefers-reduced-motion: reduce)"
      srcset="./assets/github-pulse.png"
    />
    <source
      media="(prefers-color-scheme: dark)"
      srcset="https://raw.githubusercontent.com/LiriothTeltanion/LiriothTeltanion/output/github-contribution-grid-snake-dark.svg"
    />
    <source
      media="(prefers-color-scheme: light)"
      srcset="https://raw.githubusercontent.com/LiriothTeltanion/LiriothTeltanion/output/github-contribution-grid-snake.svg"
    />
    <img
      alt="GitHub contribution snake"
      src="https://raw.githubusercontent.com/LiriothTeltanion/LiriothTeltanion/output/github-contribution-grid-snake.svg"
      width="100%"
    />
  </picture>
</div>
```

Do not add the README snippet until the first workflow run succeeds, otherwise
GitHub will temporarily show a broken image.

After enabling it, inspect the scheduled run history periodically. Disable the
workflow if upstream maintenance stops, permissions change unexpectedly or the
generated assets become unreliable. Removing the workflow does not remove the
`output` branch; remove the README snippet before intentionally deleting that
branch.
