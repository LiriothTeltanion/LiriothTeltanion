# Professional expanded GitHub profile — setup

## Required repository structure

```text
LiriothTeltanion/
├── README.md
├── assets/
│   ├── avatar.png
│   ├── profile-banner.png
│   ├── profile-banner-animated.svg
│   ├── projects/
│   │   ├── nova-music-lab.png
│   │   ├── novafit.png
│   │   ├── fullstack2026.png
│   │   └── christopher-portfolio.png
│   └── visuals/
│       ├── typing.svg
│       ├── about-me.svg
│       ├── professional-summary.svg
│       ├── tech-stack.svg
│       ├── journey.svg
│       ├── project-ecosystem.svg
│       ├── principles.svg
│       ├── creative-universe.svg
│       ├── current-focus.svg
│       ├── github-pulse.svg
│       └── footer.svg
└── extras/
```

## What changed in this edition

- Larger SVG canvases and substantially larger body text.
- Reduced decorative letter spacing to improve readability.
- More room between headings, descriptions, badges and cards.
- A recruiter-facing professional summary.
- The real email address: `kevincusnir@gmail.com`.
- Direct `mailto:` links in English, Spanish and Hebrew.
- A real email badge at the top and bottom.
- A more structured navigation line for the long profile.
- Updated animation spacing and safer initial frames.
- Matching animated and reduced-motion banner versions.

## Publish with Git

```powershell
git add README.md assets/ extras/
git commit -m "docs: improve profile typography, contact and professional summary"
git push
```

## Upload through GitHub.com

1. Open `LiriothTeltanion/LiriothTeltanion`.
2. Choose **Add file → Upload files**.
3. Replace `README.md`.
4. Upload the complete `assets` directory and preserve every subfolder.
5. Commit with:

   ```text
   docs: improve profile typography, contact and professional summary
   ```

6. Refresh the profile with `Ctrl + F5`.

## Important

Do not rename:

```text
assets/visuals/
assets/projects/
profile-banner-animated.svg
```

The README uses those exact relative paths.
