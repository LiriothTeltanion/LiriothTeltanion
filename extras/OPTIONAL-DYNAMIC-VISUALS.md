# Optional dynamic contribution animation

The main README intentionally uses only local, stable artwork. This avoids broken
images when a third-party statistics service is unavailable.

A contribution snake workflow is included as an optional enhancement:

```text
extras/snake.yml
```

## Enable it

1. Create `.github/workflows/` in your profile repository.
2. Move `extras/snake.yml` to `.github/workflows/snake.yml`.
3. Commit and push.
4. Open **Actions → Generate contribution snake → Run workflow**.
5. Wait for the workflow to create the `output` branch.
6. Add the following section only after the first successful run:

```html
## 🐍 Contribution activity

<div align="center">
  <picture>
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
