# Profile README setup

## Required repository structure

Your public profile repository must be named exactly:

```text
LiriothTeltanion
```

Place the files like this:

```text
LiriothTeltanion/
├── README.md
└── assets/
    └── profile-banner.png
```

## Publish with Git

```powershell
git add README.md assets/profile-banner.png
git commit -m "docs: redesign multilingual profile README"
git push
```

## Verify after publishing

1. Open `https://github.com/LiriothTeltanion`.
2. Confirm the banner loads.
3. Expand English, Spanish and Hebrew.
4. Confirm Hebrew reads right-to-left.
5. Test the Nova Music Lab live-demo button.
6. Confirm all four repository cards load.
7. Check the layout on desktop and mobile.

## Optional adjustments

- Remove the Christopher Rodríguez project card if the portfolio is not ready to be highlighted publicly.
- Remove PostgreSQL from the technology icon row until you have a public project demonstrating it.
- Third-party statistics services can occasionally be unavailable. The README remains useful even when those cards fail temporarily.
