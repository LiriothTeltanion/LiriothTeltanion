# Expanded visual GitHub profile — setup

## Repository structure

Upload the complete package so your profile repository contains:

```text
LiriothTeltanion/
├── README.md
├── assets/
│   ├── avatar.png
│   ├── profile-banner.png
│   ├── projects/
│   │   ├── nova-music-lab.png
│   │   ├── novafit.png
│   │   ├── fullstack2026.png
│   │   └── christopher-portfolio.png
│   └── visuals/
│       ├── typing.svg
│       ├── about-me.svg
│       ├── tech-stack.svg
│       ├── journey.svg
│       ├── project-ecosystem.svg
│       ├── principles.svg
│       ├── creative-universe.svg
│       ├── current-focus.svg
│       ├── github-pulse.svg
│       └── footer.svg
└── extras/
    ├── snake.yml
    └── OPTIONAL-DYNAMIC-VISUALS.md
```

The `extras` folder is optional. It does not run anything automatically.

## Publish with Git

```powershell
git add README.md assets/ extras/
git commit -m "docs: expand profile with original visual storytelling"
git push
```

## Upload through GitHub.com

1. Open `LiriothTeltanion/LiriothTeltanion`.
2. Choose **Add file → Upload files**.
3. Upload the new `README.md`.
4. Upload the complete `assets` directory, preserving all subfolders.
5. The `extras` directory is optional.
6. Commit with:

   ```text
   docs: expand profile with original visual storytelling
   ```

7. Refresh the public profile with `Ctrl + F5`.

## Important

The README uses relative paths. Folder names and capitalization must remain
exactly as provided.

The visual files are original and stored in your repository. They do not depend
on GitHub Readme Stats, so they will not disappear when that service is down.
