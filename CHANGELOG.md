# Changelog

All notable changes to Kevin Cusnir's public GitHub profile are documented here.
The profile follows Semantic Versioning: major for a structural identity or
presentation generation, minor for a contained feature or visual upgrade, and
patch for a narrow correction.

## [2.3.1] — 2026-07-18 · Release Integrity & Review-Gated Automation Patch

### Release status

- Published as the stable forward correction from the immutable public
  `v2.3.0` tag, using one exact finalized commit, annotated `v2.3.1` tag and
  matching non-draft, non-prerelease GitHub Release.
- Preserves the complete Profile 2.3 public identity, project evidence,
  multilingual content and visual assets.

### Fixed

- Recorded the exact Profile 2.3 release defect: public tag `v2.3.0` points to
  candidate commit `66f0436`, whose own metadata still says
  `release-candidate`, while release-state finalization reached `main` later in
  commit `44f0318`. The old tag remains immutable and this patch repairs
  forward.
- Added exact release-integrity verification so `released` metadata requires
  the current tag to point to the same finalized commit and contain matching
  released `profile.json` data.

### Changed

- Converted the scheduled Ivrit Sheli and NovaFit synchronization workflows
  from direct writes and pushes to read-only manifest drift audits.
- Added explicit read-only, `GO`, dirty-worktree, Semantic Versioning,
  beta/preview and publication boundaries to the repository workflow.
- Applied Kevin-approved GitHub account bio, canonical social-link cleanup and
  recruiter-first pin order, then verified the resulting public profile state.

### Publication boundary

- Scheduled automation can now detect stale evidence but cannot rewrite public
  profile content or publish claims under an unchanged version.
- The existing `v2.3.0` tag is not moved or deleted. Approved `v2.3.1`
  publication tags the exact finalized commit and requires public verification.

## [2.3.0] — 2026-07-18 · Verified Ivrit Synchronization Edition

### Release status

- Public tag and GitHub Release `v2.3.0` were created at candidate commit
  `66f0436` after repository checks. The tag retained candidate release
  metadata; commit `44f0318` finalized that bookkeeping on `main` afterward.
  Profile 2.3.1 preserves both commits and corrects the release process forward.
- Keeps Nova Music Lab first and preserves the complete Profile 2.2 visual and
  identity system without replacing or deleting public assets.

### Added

- Strict allow-listed synchronization from Ivrit Sheli's canonical
  `portfolio/project.json`, including a reviewed local snapshot, atomic writes,
  offline drift checks, regression tests and a scheduled/manual workflow.
- Machine-readable semantic parity checks for the Spanish and Hebrew profiles,
  covering profile/project versions, 139 backend tests, 48 frontend tests, 187
  total tests, PostgreSQL readiness, OAuth E2E status and archived media version.
- Shared workflow concurrency for NovaFit and Ivrit project synchronization so
  automated profile updates cannot race each other.

### Changed

- Advanced Ivrit Sheli public evidence from 2.1.0 to the verified live 2.2.0
  Railway deployment at commit `c8c928661bdcf179ed1d9df88b9f2e4d730ffea3`.
- Updated the verified test contract to 139 backend plus 48 frontend tests, for
  187 unique automated tests in total, with live/ready, dictionary and
  PostgreSQL readiness reported healthy in production.
- Updated English, Spanish and Hebrew recruiter-facing facts while keeping the
  final live OAuth code exchange, authenticated session refresh and logout
  explicitly unverified end to end.

### Evidence boundaries

- The live deployment, public Git tag and GitHub Release agree on Ivrit Sheli
  2.2.0, while Profile 2.3 is independently published as tag and GitHub Release
  `v2.3.0`.
- Existing Ivrit GIF/PNG interface media remains labeled as a 2.1.x archive and
  is not presented as visual proof of the live 2.2.0 interface.

## [2.2.0] — 2026-07-16 · Luminous Signature & Live Ivrit Edition

### Release status

- Published as Profile `2.2.0` from the fully validated release commit, with
  annotated tag `v2.2.0` and matching GitHub Release notes documenting the
  visual, accessibility, live-service and repository checks completed before
  launch.
- Ivrit Sheli `2.1.0` is live at
  `https://ivritsheli-production.up.railway.app`; HTTPS, readiness/version,
  PostgreSQL and the read-only synthetic demo are verified against the public
  service. GitHub OAuth consent and cancellation are verified, while the final
  authorization-code exchange remains an explicit pending check.

### Changed

- Enlarged the four-point star in the KC ✦ LT mark and lowered it toward the
  baseline so the signature reads naturally like `KC·LT` while retaining a
  distinctive handwritten star rather than a literal period.
- Increased the star's blue luminosity and blur enough to remain visible at
  compact size without obscuring the eight canonical pen strokes.
- Propagated the refined geometry through the deterministic brand masters,
  responsive banner variants and upload-ready social-preview SVG sources.
- Promoted Ivrit Sheli from deployment-ready source evidence to a linked live
  product, and advanced its verified suite to 110 backend tests plus 17
  frontend tests: 127 passing automated tests in total.

### Preserved

- The one-time reveal, static reduced-motion state and blur-free monochrome
  variant remain part of the accessibility contract.
- Project ordering, public-data boundaries and synthetic-demo safeguards remain
  unchanged from Profile `2.1.0`. The historical `2.1.0` release record below
  remains intact while the current release adds only newly verified evidence.

## [2.1.0] — 2026-07-16 · Full-Stack Production Proof & Star Signature Edition

### Release status

- Published as Profile `2.1.0` from the fully validated release commit, with
  annotated tag `v2.1.0` and matching GitHub Release notes documenting the
  visual, accessibility, privacy and repository checks completed before launch.
- Ivrit Sheli is public and deployment-ready at version `2.0.0`; a live product
  URL remains intentionally absent until its Railway deployment, TLS, readiness
  endpoint and OAuth callback have been configured and verified.

### Added

- Ivrit Sheli 2.0 as the second featured project after Nova Music Lab, with its
  public source, full-stack architecture and verified quality evidence.
- Recruiter-facing Ivrit media for desktop, responsive mobile and Hebrew RTL,
  plus a concise animated product tour with static reduced-motion fallbacks.
- A dedicated Ivrit social-preview pair and project logo for repository and
  profile presentation.
- Structured Ivrit release evidence: 109 backend tests, 17 frontend tests and
  126 unique passing automated tests in total.

### Changed

- Production evidence now includes React 19, TypeScript, FastAPI, PostgreSQL 17,
  Alembic, GitHub OAuth with PKCE, tenant RLS, Docker, integration tests and
  structured JSON logging.
- The profile growth section now moves beyond the delivered full-stack milestone
  toward monitoring and SLOs, backup/restore drills, OAuth and authorization E2E
  coverage, cost controls and incident-ready operations.
- Recommended pins now prioritize Nova Music Lab, Ivrit Sheli, NovaFit and the
  Christopher Rodríguez portfolio; Fullstack2026 remains visible as the audited
  learning archive rather than occupying a top-four product slot.
- The KC ✦ LT identity keeps eight readable blue pen strokes and adds one small
  four-point star between KC and LT with a restrained glow and reduced-motion-
  safe one-time reveal.

### Public-data and deployment boundary

- Ivrit visuals use the public read-only demonstration experience and synthetic
  learner records; they contain no private learning history, provider token,
  secret, runtime database or personal export.
- Source availability and deployment readiness are described separately from a
  live deployment. No placeholder or unverified website is presented as live.

## [2.0.0] — 2026-07-16 · NovaFit & Signature Ultimate Edition

### Release status

- Published as Profile `2.0.0` from the fully validated release commit and
  annotated tag `v2.0.0` after visual, accessibility, privacy and repository
  quality gates passed.

### Added

- Canonical `profile_version` and structured release metadata in `profile.json`.
- Semantic-version, release-tag and generated-output agreement validation.
- Recruiter-facing NovaFit 4.2.0 product-tour contract using
  `assets/novafit-product-tour.gif` with
  `assets/novafit-product-tour-static.png` for mobile and reduced motion.
- Explicit alternative text, media description and public-data boundary for the
  NovaFit tour.

### Changed

- NovaFit presentation now targets the verified 4.2.0 public facts: 124
  discovered automated tests, 12 themes, 58 public visual assets, EN/ES/HE RTL,
  verified backups, a static installable showcase and one-click Windows release.
- The KC × LT signature now uses eight clear pen strokes, a visible KC/LT
  pen-lift gap, stronger blue contrast, deterministic PNG exports and a
  reduced-motion-safe one-time drawing animation.
- Nova Music Lab remains first and remains the strongest live flagship; the
  expanded NovaFit presentation strengthens complementary Python, SQLite,
  desktop UX, analytics and release-engineering evidence.

### Public-data boundary

- NovaFit profile media uses deterministic synthetic demonstration records.
- The public profile does not publish a runtime database, private wellness
  history, personal export, secret or identity-linked metric.
- The public Pages experience remains an installable static showcase and does
  not read the local Tkinter application's desktop data.

## Pre-versioned Ultimate profile baseline — through 2026-07-15

The recruiter-first multilingual profile, responsive portrait banner, blue
KC × LT signature, Nova Music Lab flagship, four featured projects, 195-state
journey atlas, accessibility fallbacks and validation tooling were published
before formal profile-level semantic version tracking began. This is an honest
baseline description, not a retroactive `v1.0.0` tag or GitHub Release.
