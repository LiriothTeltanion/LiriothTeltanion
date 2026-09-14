# Changelog

All notable changes to Kevin Cusnir's public GitHub profile are documented here.
The profile follows Semantic Versioning: major for a structural identity or
presentation generation, minor for a contained feature or visual upgrade, and
patch for a narrow correction.

## [2.10.0] — 2026-09-14 · Reading Budget Edition — released

### Changed

- **Reading is measured in words, not lines.** The compact profile was capped at
  300 physical lines. Counted on 2026-09-13, 87 of them were HTML markup and 97
  were blank: 61 percent of the budget carried no reading at all. A `<picture>`
  cost four lines and zero seconds of attention, while one dense evidence
  sentence cost a single line and half a minute. The cap penalised exactly the
  images that help a recruiter most.
- `validate_profile.py` now counts **reading words** — prose only, with HTML
  comments, tags, link targets and Markdown punctuation removed — against
  `READING_WORD_BUDGET = 1900`. The profile reads 1767 words today.
- The line cap stays, as `STRUCTURAL_LINE_CEILING = 360`: a sanity limit on the
  shape of the file, no longer a proxy for attention.
- Both budgets are named constants in one file. `300` had been written in nine
  places — three workflows, three documents, a test and the validator twice. A
  number copied into nine places goes stale in one of them; that is precisely how
  the CV's verifier stayed red for two days while its content was correct.

### Fixed

- **NovaFit had no image visible without a click.** Its three captures sat in two
  collapsed `<details>` blocks, the same fault 2.9.0 fixed for Ivrit Sheli. The
  Command Center still now sits outside; the moving tour stays behind the toggle.
- The visible still carries its own `static_alt`, describing the Command Center
  it shows rather than borrowing the tour's description of motion.
- The visibility test now covers both projects, so neither can slip back behind
  a toggle.

## [2.9.0] — 2026-09-13 · Visible Evidence Edition — released

### Fixed

- **The Ivrit Sheli captures were invisible.** GitHub renders a `<details>`
  block collapsed, and every frame of the flagship full-stack project lived
  inside one. Anyone who merely scrolled the profile saw a picture for Nova
  Music Lab and nothing at all for the project with 1246 tests. The still Today
  screen now sits outside the toggle; the moving tour stays behind it, so
  motion is asked for and evidence is not.
- The visible caption repeated the visual-evidence boundary almost word for
  word — same version, same date, same commit, twice in one paragraph. It now
  says what the picture shows and where the other frames are, and leaves the
  proving to the boundary sentence.
- The OAuth boundary was printed verbatim twice: once in the header evidence
  line and again inside the toggle. Stated once now.

### Changed

- Three `<source>` elements were dead. In the Ivrit Sheli picture, the mobile
  and mobile-plus-reduced-motion sources named the same file, so the narrower
  one could never win. In NovaFit, all three named the same canonical still —
  that contract is enforced in the validator — so they collapse into one
  comma-separated media list that says the same thing.
- Net line count is unchanged: 300, the same budget. The payload is unchanged
  too. What moved is placement.

## [2.8.0] — 2026-09-13 · Live Visual Evidence Edition — released

### Changed

- The Ivrit Sheli spotlight now shows the **2.12.3** interface. The product
  tour, the desktop Today screen, the phone layout and the Hebrew RTL frame are
  the reviewed captures the project publishes in its own README, taken on
  2026-08-27 at commit `ea8aff866e6a`. Until now the profile argued 2.12.3 in
  prose and illustrated it with 2.2.0, then explained the gap in a footnote.
- The three still frames are stored as **PNG**, converted from the upstream
  WebP. `verify-profile.ps1` only measures and decodes `.svg`, `.png` and
  `.gif`; a `.webp` would have slipped past the payload budget instead of
  passing it. The GIF is carried over unchanged.
- `current_release_visual_proof` is `true` for the first time, so the profile
  says "current" where it used to say "archived", in all three languages.

### Fixed

- The generated caption claimed these frames "passed fresh desktop, mobile and
  Hebrew RTL browser QA". Upstream does not claim that: it reviewed them for
  privacy, hashes and byte identity, and ran a bounded smoke test before
  capturing. The sentence now states what was reviewed and names the full
  browser matrix, provider verification and deployment as separate upstream
  gates. Borrowing evidence means borrowing its limits too.
- `test_current_upstream_screenshots_do_not_promote_profile_owned_media`
  asserted that a profile still holding 2.2.0 media would end up labelled with
  the manifest's source version. That is the opposite of what the test exists to
  prove: syncing upstream facts must never silently re-badge the profile's own
  captures as belonging to a release they do not show.

## [2.7.0] — 2026-09-13 · Current Deployment Edition — released

### Fixed

- The Ivrit Sheli synchronizer read a manifest schema the project had already
  left behind, so it stopped reading anything and failed daily for weeks. The
  profile kept advertising July: version 2.4.0, 213 tests, and a Railway demo
  link that answers **HTTP 404**. It now reads the current contract.
- `PROFILE_ES.md` and `PROFILE_HE.md` are maintained by hand and had drifted the
  same way. Both carry the reviewed figures again.
- The external-link audit treated an address the profile itself records as
  retired as a broken link, so it stayed red for being accurate. A real broken
  link is easy to miss in that noise, which is what happened. Retired addresses
  are now skipped by name.

### Changed

- Ivrit Sheli facts: **2.12.3** source, **387 backend + 859 frontend = 1246**
  verified automated tests, and a reachable demo at `ivrit-sheli.onrender.com`.
- The project is described as a **private candidate with a staging demo**, not a
  production release. The published release remains v2.12.2. Updating the facts
  was not taken as licence to upgrade the claim.
- Neither the hosting provider, the environment nor the demo address are written
  into the code any more; every published sentence is built from the manifest.
  Hard-coding them is what let a retired address survive in public for a month.
- The validator checks the fields the profile publishes and tolerates fields it
  does not read, so a future schema that only adds information cannot take the
  profile offline again. A schema change is still refused outright.

### Added

- A check that refuses to publish, as the live demo, the address the manifest
  marks as retired.
- One shared function builds the public status sentence for both the generator
  and the synchronizer, so the sentence published and the sentence demanded
  cannot drift apart.

## [2.6.0] — 2026-08-09 · Living Archive Clarity Edition — released

### Added

- Nova Music Lab 1.6.0 desktop, mobile, animated, reduced-motion and social-card
  media promoted from its checksum-verified deployed release contract.
- Recruiter-facing evidence for the complete Artist Atlas navigator, clearer
  public-museum/build-your-own journey and more understandable interpretive
  boundaries.

### Changed

- Advanced the flagship to Nova Music Lab 1.6.0, deployed 2026-08-09. GitHub
  Pages serves commit `eb7b27cd08c19634ab5c1976facb4b221701ea43`; the product
  tag points to commit `e0d49d2940343fe2ebd7cfb4eee4cbd4d8d39cae`.
- Updated the public archive evidence to 82,661 plays, 20,908 tracks and 6,593
  exact-name catalog entries without presenting catalog variants as unique
  people.
- Updated genre evidence to 94.2% classified plays and 457 entries with
  detailed evidence, kept separate from automatic classification.
- Updated engineering evidence to 803 passing tests, one intentional private-
  fixture skip and 18/18 passing Playwright journeys.
- Synchronized the generated English profile and reviewed Spanish and Hebrew
  summaries while preserving every unrelated Ivrit Sheli, NovaFit and identity
  claim.

### Evidence boundaries

- Only the five release-manifest media IDs consumed by the public profile are
  duplicated here. Atlas, Genres, Guest Museum and Hebrew Share captures remain
  in Nova Music Lab's own release gallery.
- Private listening exports remain in the browser; this profile publishes only
  aggregate public evidence and sanitized release visuals.
- The served Pages commit and product tag commit are recorded separately rather
  than being presented as the same artifact.

### Release status

- Kevin explicitly approved publication on 2026-08-09. The exact `released`
  commit is promoted only after the full profile gate and pull-request checks;
  annotated tag `v2.6.0` and its GitHub Release must target that same commit.

## [2.5.0] — 2026-08-01 · Living Flagship Evidence Edition — released

### Added

- A strict Nova Music Lab deployed-release contract sourced from the live
  GitHub Pages manifest, with cache bypass, exact commit pinning, bounded media
  downloads, SHA-256 and raster-dimension verification, an ignored review
  candidate and a read-only drift workflow.
- Nova Music Lab 1.5.0 desktop, mobile, animated, reduced-motion and social-card
  media selected from the deployed release package.
- Regression coverage for stale manifests, candidate/deployed boundaries,
  invalid dates, media tampering, unsafe paths and manual workflow behavior.

### Changed

- Advanced the flagship to Nova Music Lab 1.5.0, deployed 2026-08-01 at commit
  `5c1d57048b52d41819a7d0af4d577a4bbe60064d`, with 711 passing tests, one
  intentional skip, 18 passing Playwright journeys and successful CI, privacy,
  media, bundle and Pages smoke gates.
- Reframed the product around its Living Artist Atlas, transparent genre
  provenance, 6,413 catalog rows, 94.1% analytical play coverage and local-only
  private imports.
- Advanced Ivrit Sheli evidence to the deployed and published 2.4.0 contract:
  151 backend + 62 frontend = 213 passing tests, with Google live sign-in and
  the remaining GitHub-session/re-login boundaries stated explicitly.
- Synchronized the generated English profile and the human-reviewed Spanish
  and Hebrew summaries without replacing the established identity system.

### Evidence boundaries

- Nova release media was captured from the final private candidate before
  publication. The live manifest, deployed commit and CI prove the later public
  state; the candidate label remains visible rather than being edited away.
- Ivrit Sheli 2.2.0 screenshots remain archived interaction history and are not
  presented as visual proof of the live 2.4.0 interface.
- All project synchronization remains review-gated; scheduled workflows detect
  drift but never commit or publish public-profile changes automatically.

### Release status

- Finalized after Kevin's explicit publication approval as the exact `released`
  commit for annotated tag `v2.5.0` and its stable GitHub Release.
- Candidate and GitHub Actions validation passed before finalization; the tag,
  branch and release are published together only after the exact-tag verifier.

## [2.4.0] — 2026-07-18 · Recruiter Visual Evidence Edition — released

### Added

- Fresh live Ivrit Sheli 2.2.0 desktop, 390-pixel mobile and Hebrew RTL
  captures, inspected against the deployed Railway interface.
- A current 2.2 social-preview SVG/PNG pair with the verified 187-test claim.
- Regression coverage that keeps stronger profile-owned visual evidence when
  the independently review-gated upstream manifest still reports older media.
- Live deployment evidence records Railway runtime build `66d68a3c44ac` and its
  verified release application baseline `c8c928661bdc`; captures carry both
  commit provenance and the visual-QA date.

### Improved

- Corrected the external-link extractor so Markdown inline-code backticks can
  no longer create false 404 results for verified public profile URLs.
- Rebuilt the Ivrit product-tour GIF from three current live frames at a much
  smaller payload while retaining static reduced-motion fallbacks.
- Reduced the NovaFit tour from 3,914,571 to 548,594 bytes while preserving its
  960 x 595 canvas, nine-second duration and five core recruiter-facing scenes.
- Updated English, Spanish and Hebrew visual-evidence wording without changing
  the honest OAuth exchange, session-refresh or logout boundary.
- Published independently versioned visual upgrades for CV 1.1.0, Christopher
  Rodríguez Portfolio 1.1.0 and Fullstack2026 1.1.1, including the latter's
  forward security correction after its initial 1.1.0 release.

### Release status

- Published as the stable `v2.4.0` GitHub Release from the exact finalized and
  validated release commit after Kevin's explicit approval.
- Applied and publicly verified repository descriptions, websites and topics,
  seven 1280 x 640 social previews and the fourth Exophase account link.

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
