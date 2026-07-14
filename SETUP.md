# Ultimate animated GitHub profile — setup

## Required repository structure

```text
LiriothTeltanion/
├── README.md
├── assets/
│   ├── avatar.png
│   ├── profile-banner.png
│   ├── profile-banner-animated.svg
│   ├── projects/
│   │   ├── nova-music-lab.svg
│   │   ├── novafit.svg
│   │   ├── fullstack2026.svg
│   │   └── christopher-portfolio.svg
│   └── visuals/
│       ├── typing.svg
│       ├── executive-dashboard.svg
│       ├── professional-summary.svg
│       ├── about-me.svg
│       ├── language-profile.svg
│       ├── experience-bridge.svg
│       ├── journey.svg
│       ├── tech-stack.svg
│       ├── project-matrix.svg
│       ├── project-ecosystem.svg
│       ├── principles.svg
│       ├── creative-universe.svg
│       ├── current-focus.svg
│       ├── github-pulse.svg
│       └── footer.svg
└── extras/
```

## Major improvements in this edition

- Animated executive graphs placed near the top.
- Evidence-based capability bars rather than invented proficiency percentages.
- Animated portfolio-composition donut.
- Detailed language and communication profile.
- Transferable-experience bridge connecting repair work, service, training and product development.
- Animated project capability matrix.
- Animated SVG project cards replacing static PNG cards.
- Larger typography and safer spacing throughout.
- Fuller English, Spanish and Hebrew profile content.
- Beersheba, Israel added to the professional location.
- Real clickable email: `kevincusnir@gmail.com`.
- More detailed descriptions of technologies, projects, principles, strengths and roadmap.
- Local SVG assets to avoid fragile third-party statistics cards.

## Publish with Git

```powershell
git add README.md assets/ extras/
git commit -m "docs: publish ultimate animated multilingual profile"
git push
```

## Upload through GitHub.com

1. Open `LiriothTeltanion/LiriothTeltanion`.
2. Select **Add file → Upload files**.
3. Replace `README.md`.
4. Upload the complete `assets` folder.
5. Preserve every subfolder and exact filename.
6. Commit with:

   ```text
   docs: publish ultimate animated multilingual profile
   ```

7. Refresh the public profile with `Ctrl + F5`.

## Reduced motion

The animated header has a PNG fallback for users who request reduced motion:

```html
<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/profile-banner.png" />
  <img src="./assets/profile-banner-animated.svg" />
</picture>
```

## Important

Do not rename the following folders:

```text
assets/visuals/
assets/projects/
```

The README uses exact relative paths.


## Final header polish

The main animated header now uses:

```text
KEVIN CUSNIR
(LIRIOTHTELTANION)
```

The name font was reduced and the underline shortened so the complete identity
remains readable at GitHub's rendered profile width.
