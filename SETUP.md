# Profile README setup — stable visual edition

## Required repository structure

```text
LiriothTeltanion/
├── README.md
└── assets/
    ├── profile-banner.png
    ├── github-pulse.png
    └── projects/
        ├── nova-music-lab.png
        ├── novafit.png
        ├── fullstack2026.png
        └── christopher-portfolio.png
```

## Why the previous cards were missing

The former cards depended on `github-readme-stats.vercel.app`.
That external service failed to return the images, so GitHub showed their
alternative text instead. These replacement cards are stored directly in
your repository and do not depend on that service.

## Publish with Git

```powershell
git add README.md assets/
git commit -m "fix(profile): replace broken external cards with local artwork"
git push
```

## Upload through GitHub.com

1. Open `LiriothTeltanion/LiriothTeltanion`.
2. Choose **Add file → Upload files**.
3. Upload the new `README.md`.
4. Drag the complete `assets` folder, including `assets/projects`.
5. Commit with:
   `fix(profile): replace broken external cards with local artwork`
6. Refresh your public profile with `Ctrl + F5`.

## Verify

- Four project cards appear in two rows.
- Every card opens the correct repository.
- The GitHub pulse image appears near the bottom.
- English, Spanish and Hebrew remain collapsible.
- No “repository card” text appears in place of an image.
