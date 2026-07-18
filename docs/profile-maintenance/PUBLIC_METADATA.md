# Approved GitHub metadata blueprint

This file is the exact, evidence-based configuration for Kevin's public GitHub
repositories. Keeping the blueprint here does not apply account settings by
itself: About metadata, social previews and pinned repositories still require a
reviewed GitHub update and a public verification pass.

## Profile repository: `LiriothTeltanion/LiriothTeltanion`

**Description**

```text
Multilingual developer profile for Kevin Cusnir (Lirioth Teltanion): React, TypeScript, Python, PostgreSQL, accessible RTL UX, local-first products, and creative technology.
```

**Website**

```text
https://liriothteltanion.github.io/NovaMusicLab/
```

This intentionally points to the verified live flagship. The old profile Pages
URL returns 404 and must not be restored unless a real site is deployed there.

**Topics**

```text
github-profile
developer-portfolio
full-stack
frontend-development
react
typescript
accessibility
multilingual
local-first
creative-technology
python
postgresql
fastapi
docker
rtl
```

**Social preview after upload**

```text
assets/social/profile-social-preview.png
```

**Alt text**

```text
Kevin Cusnir and the Lirioth Teltanion creative identity presented in a blue developer-profile card with React, TypeScript, Python, PostgreSQL, accessible RTL UX and multilingual product focus.
```

**Public boundary**

The card uses Kevin's intentionally public profile identity and portfolio facts.
It does not contain private contact details beyond the email already published
in the profile, personal documents, private metrics or unverified claims.

## `LiriothTeltanion/NovaMusicLab`

**Description**

```text
Local-first React and TypeScript music museum that turns Spotify, Last.fm, Apple Music, ListenBrainz, and YouTube exports into source-aware analytics.
```

**Website**

```text
https://liriothteltanion.github.io/NovaMusicLab/
```

**Topics**

```text
react
typescript
music-analytics
data-visualization
local-first
accessibility
vite
vitest
github-pages
```

**Social preview after upload**

```text
assets/social/novamusiclab-social-preview.png
```

## `LiriothTeltanion/IvritSheli`

**Description**

```text
Ivrit Sheli 2.2.0 is a live trilingual Hebrew-learning PWA with FastAPI, PostgreSQL/RLS, Docker, structured logging and 187 verified tests.
```

**Website**

```text
https://ivritsheli-production.up.railway.app
```

This is the verified Railway deployment. `/health/live`, `/health/ready`,
`/version`, the PostgreSQL-backed runtime and dictionary readiness passed public
QA at production commit `c8c928661bdcf179ed1d9df88b9f2e4d730ffea3`. OAuth
consent and safe cancellation passed; the final authorization-code exchange,
authenticated session refresh and logout remain pending end-to-end checks.

**Topics**

```text
hebrew-learning
full-stack
react
typescript
fastapi
postgresql
docker
github-oauth
row-level-security
integration-testing
structured-logging
internationalization
rtl
accessibility
local-first
pwa
```

**Archived social preview — do not upload as current 2.2 proof**

```text
assets/social/ivrit-sheli-social-preview.png
```

The tracked SVG/PNG pair still displays 2.1 and 127-test copy. Keep it as
provenance until a synchronized 2.2 replacement is rendered and visually
checked. The metadata below is the target for that future current preview.

**Alt text**

```text
Ivrit Sheli 2.2.0 product card presenting a live trilingual Hebrew-learning service with Railway, PostgreSQL tenant isolation, Docker, structured logging and 187 verified tests.
```

**Public boundary**

The archived profile tour uses the shared read-only demonstration experience
and synthetic learner records. It contains no private learning history,
provider token, secret, runtime database or personal export, but it represents
the 2.1.x interface rather than current 2.2 visual proof. The live label is
limited to the verified Railway service; the final OAuth authorization-code
exchange, session refresh and logout remain explicitly pending.

## `LiriothTeltanion/NovaFit`

**Description**

```text
NovaFit 4.2.0 is a local-first Python, Tkinter and SQLite wellness studio with EN/ES/HE RTL UX, explainable analytics, 124 tests and Windows releases.
```

**Website**

```text
https://liriothteltanion.github.io/NovaFit/
```

This URL is the verified installable static showcase. It presents deterministic
demonstration data and links to the desktop download; it is not the Tkinter
runtime and cannot read or publish the local desktop database.

**Topics**

```text
python
tkinter
sqlite
local-first
wellness
internationalization
rtl
analytics
testing
windows
github-pages
pwa
```

**Social preview after upload**

```text
assets/social/novafit-social-preview.png
```

**Alt text**

```text
NovaFit 4.2.0 blue product card highlighting a local-first Windows wellness studio, four analytics spaces, EN/ES/HE RTL support, 12 themes and 124 automated tests.
```

**Public boundary**

The preview and linked showcase use clearly labeled demo profiles and
deterministic synthetic records. They contain no real wellness history, private
profile, runtime database, secret, medical claim or private export.

## `LiriothTeltanion/ChristopherRodriguezCVOnline`

**Description**

```text
Accessible bilingual React and TypeScript portfolio for an English educator, with verified-content states, persistent themes, and GitHub Pages delivery.
```

**Website**

```text
https://liriothteltanion.github.io/ChristopherRodriguezCVOnline/
```

**Topics**

```text
react
typescript
portfolio
bilingual
accessibility
tailwind-css
framer-motion
github-pages
```

**Social preview after upload**

```text
assets/social/christopherrodriguezcvonline-social-preview.png
```

## `LiriothTeltanion/Fullstack2026`

**Description**

```text
Six-week full-stack learning archive covering Python, JavaScript, TypeScript, SQL, Node.js, tests, CI, and transparent repository audits.
```

Leave the website empty. This is explicitly a learning archive with documented
remaining quality gates, not a finished deployed product.

**Topics**

```text
full-stack
learning-archive
python
javascript
typescript
nodejs
sql
testing
github-actions
```

**Social preview after upload**

```text
assets/social/fullstack2026-social-preview.png
```

## Recommended profile pins

Use this order so the strongest working evidence appears first:

1. `NovaMusicLab` — live frontend and data flagship.
2. `IvritSheli` — live authenticated full-stack product with PostgreSQL.
3. `NovaFit` — complete Python desktop and SQLite product.
4. `ChristopherRodriguezCVOnline` — accessible real-world collaboration.

Keep `Fullstack2026` public and linked from the README as transparent learning
progression, but outside the top four pins now that stronger product evidence is
available.

Unpin the profile repository itself; its README is already the page recruiters
are viewing and that pin currently consumes a higher-value project slot.

## Publication checklist

1. Obtain Kevin's explicit final publish approval.
2. Commit and push the validated local profile changes.
3. Update each About panel with the exact description, website and topics above.
   Keep Ivrit's verified Railway website URL visible.
4. Upload only a matching, current 1280 x 640 PNG under **Settings → General → Social preview**. Do not upload the archived Ivrit 2.1/127-test pair as current 2.2 proof.
5. Reorder the four profile pins to Nova Music Lab, Ivrit Sheli, NovaFit and
   Christopher Rodríguez Portfolio, then unpin the profile repository.
6. Refresh every public repository in a signed-out window and confirm the
   descriptions, preview crops, working websites and pin order.

Do not replace a verified URL with a placeholder and do not add employment,
adoption, certification, user-count or performance claims without evidence.
