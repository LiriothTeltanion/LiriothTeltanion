"""Synchronize verified Ivrit Sheli facts into the generated GitHub profile.

The remote project manifest is untrusted input. Only the exact allow-listed URL,
strict schema and bounded fields below can update the canonical Ivrit project.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

if __package__:
    from scripts import build_profile
else:
    import build_profile

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = ROOT / "profile.json"
DEFAULT_SNAPSHOT = ROOT / "data" / "project-snapshots" / "ivrit-sheli.json"
DEFAULT_COMPACT_OUTPUT = ROOT / "README.md"
DEFAULT_EXPANDED_OUTPUT = ROOT / "README_EXPANDED.md"
DEFAULT_MANIFEST_URL = (
    "https://raw.githubusercontent.com/"
    "LiriothTeltanion/IvritSheli/main/portfolio/project.json"
)
EXPECTED_REPOSITORY = "https://github.com/LiriothTeltanion/IvritSheli"
EXPECTED_DEMO = "https://ivritsheli-production.up.railway.app"
EXPECTED_MANIFEST_NAME = "Ivrit Sheli — העברית שלי"
EXPECTED_SCHEMA = "ivrit-sheli-portfolio-project-v1"
EXPECTED_TEST_REPORT = f"{EXPECTED_REPOSITORY}/blob/main/TEST_REPORT.md"
MAX_MANIFEST_BYTES = 512 * 1024
REQUEST_HEADERS = {
    "User-Agent": "Lirioth-profile-sync/2.3",
    "Cache-Control": "no-cache, no-store, max-age=0",
    "Pragma": "no-cache",
}
VERSION_PATTERN = re.compile(r"^[0-9]+(?:\.[0-9]+){2}(?:[-+][0-9A-Za-z.-]+)?$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")

TOP_LEVEL_FIELDS = {
    "schema",
    "slug",
    "name",
    "source_version",
    "live_version",
    "status",
    "default_branch",
    "repository_url",
    "demo_url",
    "summary",
    "languages",
    "stack",
    "tests",
    "deployment",
    "publication",
    "visual_proof",
    "oauth",
    "privacy",
}
TEST_FIELDS = {
    "backend_unique",
    "frontend",
    "frontend_files",
    "total_unique",
    "ordinary_backend_passed",
    "ordinary_backend_skipped",
    "postgresql_gate_passed",
    "evidence",
}
DEPLOYMENT_FIELDS = {
    "provider",
    "runtime",
    "database",
    "status",
    "production_commit",
    "verified_on",
    "environment",
    "health_live",
    "health_ready",
    "postgresql_ready",
    "dictionary_ready",
}
PUBLICATION_FIELDS = {
    "latest_git_tag",
    "latest_github_release",
    "source_version_tagged",
    "source_version_github_release_published",
    "release_state",
}
VISUAL_PROOF_FIELDS = {
    "state",
    "social_preview_version",
    "readme_screenshot_version",
    "readme_screenshots_match_live_version",
    "live_2_2_interactive_browser_qa",
}
OAUTH_FIELDS = {
    "provider",
    "consent_handoff_verified",
    "cancellation_verified",
    "final_live_code_exchange_verified",
    "authenticated_session_refresh_verified",
    "logout_verified",
    "boundary",
}
PRIVACY_FIELDS = {
    "local_first",
    "public_demo_data",
    "public_demo_mutations",
    "contains_secrets",
}


def build_parser() -> argparse.ArgumentParser:
    """Create the synchronization command-line interface."""
    parser = argparse.ArgumentParser(
        description="Sync Ivrit Sheli's public manifest into this profile."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--url",
        default=None,
        help="Fetch the manifest from Ivrit Sheli's allow-listed raw GitHub URL.",
    )
    source.add_argument("--manifest", type=Path, help="Read a local manifest file.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write", action="store_true", help="Update the snapshot and profile."
    )
    mode.add_argument(
        "--check", action="store_true", help="Fail when generated files drift."
    )
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--compact-output", type=Path, default=DEFAULT_COMPACT_OUTPUT)
    parser.add_argument("--expanded-output", type=Path, default=DEFAULT_EXPANDED_OUTPUT)
    return parser


def load_manifest(path: Path) -> dict[str, Any]:
    """Load a size-limited local manifest and validate its complete contract."""
    payload = path.read_bytes()
    if len(payload) > MAX_MANIFEST_BYTES:
        raise ValueError(f"Manifest exceeds {MAX_MANIFEST_BYTES} bytes.")
    return validate_manifest(_decode_object(payload, str(path)))


def fetch_manifest(url: str, timeout: float = 15.0) -> dict[str, Any]:
    """Fetch the sole allow-listed raw manifest with a bounded network read."""
    if url != DEFAULT_MANIFEST_URL:
        raise ValueError(
            "Only Ivrit Sheli's canonical raw GitHub manifest URL is allowed."
        )
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise ValueError("Manifest URL must use HTTPS on raw.githubusercontent.com.")
    fresh_url = f"{url}?profile-sync={time.time_ns()}"
    request = Request(fresh_url, headers=REQUEST_HEADERS)
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - exact allow-list
        advertised = response.headers.get("Content-Length")
        if advertised is not None and int(advertised) > MAX_MANIFEST_BYTES:
            raise ValueError(f"Manifest exceeds {MAX_MANIFEST_BYTES} bytes.")
        payload = response.read(MAX_MANIFEST_BYTES + 1)
    if len(payload) > MAX_MANIFEST_BYTES:
        raise ValueError(f"Manifest exceeds {MAX_MANIFEST_BYTES} bytes.")
    return validate_manifest(_decode_object(payload, url))


def _decode_object(payload: bytes, source: str) -> dict[str, Any]:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Manifest is not valid UTF-8 JSON: {source}") from error
    if not isinstance(data, dict):
        raise ValueError("Manifest root must be an object.")
    return data


def validate_manifest(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate identity, exact keys, types, arithmetic and truth boundaries."""
    _exact_keys(raw, TOP_LEVEL_FIELDS, "manifest")
    _expect(raw.get("schema") == EXPECTED_SCHEMA, "Unexpected manifest schema.")
    _expect(raw.get("slug") == "ivrit-sheli", "Unexpected project slug.")
    _expect(raw.get("name") == EXPECTED_MANIFEST_NAME, "Unexpected project name.")
    _expect(raw.get("status") == "live", "Ivrit Sheli manifest is not live.")
    _expect(raw.get("default_branch") == "main", "Default branch must be main.")
    _expect(
        raw.get("repository_url") == EXPECTED_REPOSITORY,
        "Unexpected repository URL.",
    )
    _expect(raw.get("demo_url") == EXPECTED_DEMO, "Unexpected live demo URL.")

    source_version = _semantic_version(raw.get("source_version"), "source_version")
    live_version = _semantic_version(raw.get("live_version"), "live_version")
    _expect(
        source_version == live_version,
        "Source and verified live versions must match before profile publication.",
    )
    _plain_text(raw.get("summary"), "summary", 600)
    languages = _plain_text_list(raw.get("languages"), "languages", 10, 12)
    _expect(set(languages) == {"en", "es", "he"}, "Languages must be en, es and he.")
    stack = _plain_text_list(raw.get("stack"), "stack", 16, 60)
    _expect(len(stack) >= 5, "Stack must contain at least five technologies.")

    tests = _mapping(raw.get("tests"), "tests")
    _exact_keys(tests, TEST_FIELDS, "tests")
    backend = _bounded_int(tests.get("backend_unique"), "tests.backend_unique", 1, 100_000)
    frontend = _bounded_int(tests.get("frontend"), "tests.frontend", 1, 100_000)
    total = _bounded_int(tests.get("total_unique"), "tests.total_unique", 1, 200_000)
    ordinary_passed = _bounded_int(
        tests.get("ordinary_backend_passed"),
        "tests.ordinary_backend_passed",
        0,
        100_000,
    )
    ordinary_skipped = _bounded_int(
        tests.get("ordinary_backend_skipped"),
        "tests.ordinary_backend_skipped",
        0,
        100_000,
    )
    _bounded_int(tests.get("frontend_files"), "tests.frontend_files", 1, 10_000)
    _bounded_int(
        tests.get("postgresql_gate_passed"),
        "tests.postgresql_gate_passed",
        1,
        10_000,
    )
    _expect(total == backend + frontend, "Total tests must equal backend plus frontend.")
    _expect(
        ordinary_passed + ordinary_skipped == backend,
        "Ordinary backend passed plus skipped must equal backend_unique.",
    )
    _expect(tests.get("evidence") == "TEST_REPORT.md", "Unexpected test evidence path.")

    deployment = _mapping(raw.get("deployment"), "deployment")
    _exact_keys(deployment, DEPLOYMENT_FIELDS, "deployment")
    for field, expected in (
        ("provider", "Railway"),
        ("runtime", "Docker"),
        ("database", "PostgreSQL 17"),
        ("status", "verified"),
        ("environment", "production"),
    ):
        _expect(deployment.get(field) == expected, f"Unexpected deployment.{field}.")
    commit = _plain_text(
        deployment.get("production_commit"), "deployment.production_commit", 40
    )
    _expect(bool(COMMIT_PATTERN.fullmatch(commit)), "Production commit must be a full SHA-1.")
    _iso_date(deployment.get("verified_on"), "deployment.verified_on")
    for field in ("health_live", "health_ready", "postgresql_ready", "dictionary_ready"):
        _expect(deployment.get(field) is True, f"deployment.{field} must be true.")

    publication = _mapping(raw.get("publication"), "publication")
    _exact_keys(publication, PUBLICATION_FIELDS, "publication")
    latest_tag = _release_tag(publication.get("latest_git_tag"), "publication.latest_git_tag")
    latest_release = _release_tag(
        publication.get("latest_github_release"),
        "publication.latest_github_release",
    )
    for field in ("source_version_tagged", "source_version_github_release_published"):
        _boolean(publication.get(field), f"publication.{field}")
    release_state = publication.get("release_state")
    _expect(
        release_state
        in {"deployment-ahead-of-github-release", "published-and-deployed"},
        "Unexpected publication.release_state.",
    )
    if release_state == "deployment-ahead-of-github-release":
        _expect(
            publication["source_version_tagged"] is False
            and publication["source_version_github_release_published"] is False,
            "Deployment-ahead state requires unpublished source tag and release flags.",
        )
        _expect(
            latest_tag != f"v{source_version}" and latest_release != f"v{source_version}",
            "Deployment-ahead state cannot claim a current tag or release.",
        )
    else:
        _expect(
            publication["source_version_tagged"] is True
            and publication["source_version_github_release_published"] is True,
            "Published-and-deployed state requires current tag and release flags.",
        )
        _expect(
            latest_tag == f"v{source_version}"
            and latest_release == f"v{source_version}",
            "Published-and-deployed state must match the source version.",
        )

    visual = _mapping(raw.get("visual_proof"), "visual_proof")
    _exact_keys(visual, VISUAL_PROOF_FIELDS, "visual_proof")
    _expect(visual.get("state") in {"partial", "current"}, "Unexpected visual proof state.")
    social_preview_version = _semantic_version(
        visual.get("social_preview_version"),
        "visual_proof.social_preview_version",
    )
    _expect(
        social_preview_version == source_version,
        "Social preview version must match the source version.",
    )
    screenshot_version = _plain_text(
        visual.get("readme_screenshot_version"),
        "visual_proof.readme_screenshot_version",
        40,
    )
    _expect(
        bool(re.fullmatch(r"[0-9]+\.[0-9]+\.(?:[0-9]+|x)", screenshot_version)),
        "README screenshot version must be a semantic version or x patch series.",
    )
    _boolean(
        visual.get("readme_screenshots_match_live_version"),
        "visual_proof.readme_screenshots_match_live_version",
    )
    _expect(
        visual.get("live_2_2_interactive_browser_qa") in {"pending", "verified"},
        "Unexpected live 2.2 browser QA state.",
    )
    if visual["readme_screenshots_match_live_version"]:
        _expect(
            screenshot_version == live_version,
            "Screenshots marked current must match the live semantic version.",
        )
        _expect(visual["state"] == "current", "Current screenshots require current visual proof.")
        _expect(
            visual["live_2_2_interactive_browser_qa"] == "verified",
            "Current screenshots require verified interactive browser QA.",
        )
    else:
        _expect(visual["state"] == "partial", "Stale screenshots require partial visual proof.")

    oauth = _mapping(raw.get("oauth"), "oauth")
    _exact_keys(oauth, OAUTH_FIELDS, "oauth")
    _expect(oauth.get("provider") == "GitHub", "Unexpected OAuth provider.")
    _expect(oauth.get("consent_handoff_verified") is True, "OAuth consent handoff must be verified.")
    _expect(oauth.get("cancellation_verified") is True, "OAuth cancellation must be verified.")
    for field in (
        "final_live_code_exchange_verified",
        "authenticated_session_refresh_verified",
        "logout_verified",
    ):
        _expect(oauth.get(field) is False, f"oauth.{field} must remain false until verified.")
    _plain_text(oauth.get("boundary"), "oauth.boundary", 500)

    privacy = _mapping(raw.get("privacy"), "privacy")
    _exact_keys(privacy, PRIVACY_FIELDS, "privacy")
    _expect(privacy.get("local_first") is True, "Ivrit Sheli must retain a local-first mode.")
    _expect(privacy.get("public_demo_data") == "synthetic", "Public demo data must be synthetic.")
    _expect(
        privacy.get("public_demo_mutations") == "server-blocked",
        "Public demo mutations must be server-blocked.",
    )
    _expect(privacy.get("contains_secrets") is False, "Manifest must not contain secrets.")
    return copy.deepcopy(dict(raw))


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object.")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unexpected {', '.join(extra)}")
        raise ValueError(f"{path} fields are invalid: {'; '.join(details)}.")


def _plain_text(value: Any, path: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{path} must be non-empty plain text up to {maximum} characters.")
    if value != value.strip() or any(character in value for character in "\r\n<>[]|"):
        raise ValueError(f"{path} contains unsafe Markdown or control characters.")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{path} contains control characters.")
    return value


def _plain_text_list(value: Any, path: str, maximum_items: int, maximum_text: int) -> list[str]:
    if not isinstance(value, list) or not value or len(value) > maximum_items:
        raise ValueError(f"{path} must be a non-empty array of at most {maximum_items} items.")
    result = [
        _plain_text(item, f"{path}[{index}]", maximum_text)
        for index, item in enumerate(value)
    ]
    if len({item.casefold() for item in result}) != len(result):
        raise ValueError(f"{path} contains duplicate values.")
    return result


def _bounded_int(value: Any, path: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{path} must be an integer from {minimum} through {maximum}.")
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{path} must be boolean.")
    return value


def _semantic_version(value: Any, path: str) -> str:
    version = _plain_text(value, path, 40)
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(f"{path} is not a semantic version.")
    return version


def _release_tag(value: Any, path: str) -> str:
    tag = _plain_text(value, path, 41)
    if not tag.startswith("v") or not VERSION_PATTERN.fullmatch(tag[1:]):
        raise ValueError(f"{path} must be a v-prefixed semantic version.")
    return tag


def _iso_date(value: Any, path: str) -> str:
    text = _plain_text(value, path, 10)
    try:
        date.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{path} must be a valid YYYY-MM-DD date.") from error
    return text


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def apply_manifest(profile: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy with only the canonical Ivrit project synchronized."""
    validated = validate_manifest(manifest)
    updated = copy.deepcopy(dict(profile))
    projects = updated.get("projects")
    if not isinstance(projects, list):
        raise ValueError("profile.projects must be an array.")
    matches = [
        project
        for project in projects
        if isinstance(project, dict)
        and project.get("name") == "Ivrit Sheli"
        and project.get("source") == EXPECTED_REPOSITORY
    ]
    if len(matches) != 1:
        raise ValueError("Profile must contain exactly one canonical Ivrit Sheli project.")

    project = matches[0]
    tests = validated["tests"]
    deployment = validated["deployment"]
    publication = validated["publication"]
    visual = validated["visual_proof"]
    oauth = validated["oauth"]
    source_version = validated["source_version"]
    live_version = validated["live_version"]
    project["status"] = f"Live v{live_version} dual-mode full-stack product"
    project["solution"] = validated["summary"]
    project["stack"] = " · ".join(validated["stack"])
    project["demo"] = validated["demo_url"]
    project["evidence"] = (
        f"Verified Railway production and PostgreSQL readiness at commit "
        f"{deployment['production_commit'][:12]}, with {tests['backend_unique']} backend + "
        f"{tests['frontend']} frontend = {tests['total_unique']} passing tests; GitHub OAuth "
        "consent handoff and cancellation are verified, while final live code exchange, "
        "session refresh and logout remain unverified end to end"
    )
    project["release_evidence"] = {
        "version": source_version,
        "backend_tests": tests["backend_unique"],
        "frontend_tests": tests["frontend"],
        "total_tests": tests["total_unique"],
        "test_report": EXPECTED_TEST_REPORT,
    }
    project["portfolio_sync"] = {
        "schema": EXPECTED_SCHEMA,
        "source": DEFAULT_MANIFEST_URL,
        "source_version": source_version,
        "live_version": live_version,
        "backend_tests": tests["backend_unique"],
        "frontend_tests": tests["frontend"],
        "total_tests": tests["total_unique"],
        "test_report": EXPECTED_TEST_REPORT,
        "demo_url": validated["demo_url"],
        "provider": deployment["provider"],
        "runtime": deployment["runtime"],
        "database": deployment["database"],
        "production_commit": deployment["production_commit"],
        "verified_on": deployment["verified_on"],
        "environment": deployment["environment"],
        "health_live": deployment["health_live"],
        "health_ready": deployment["health_ready"],
        "postgresql_ready": deployment["postgresql_ready"],
        "dictionary_ready": deployment["dictionary_ready"],
        "latest_git_tag": publication["latest_git_tag"],
        "latest_github_release": publication["latest_github_release"],
        "source_version_tagged": publication["source_version_tagged"],
        "source_version_github_release_published": publication[
            "source_version_github_release_published"
        ],
        "release_state": publication["release_state"],
        "visual_proof_state": visual["state"],
        "social_preview_version": visual["social_preview_version"],
        "readme_screenshot_version": visual["readme_screenshot_version"],
        "readme_screenshots_match_live_version": visual[
            "readme_screenshots_match_live_version"
        ],
        "live_2_2_interactive_browser_qa": visual[
            "live_2_2_interactive_browser_qa"
        ],
        "oauth_final_live_code_exchange_verified": oauth[
            "final_live_code_exchange_verified"
        ],
        "authenticated_session_refresh_verified": oauth[
            "authenticated_session_refresh_verified"
        ],
        "logout_verified": oauth["logout_verified"],
        "oauth_boundary": oauth["boundary"],
    }
    media = project.get("media")
    if not isinstance(media, dict):
        raise ValueError("Canonical Ivrit Sheli project must retain its media mapping.")
    media.update(
        {
            "version": visual["readme_screenshot_version"],
            "current_release_visual_proof": visual[
                "readme_screenshots_match_live_version"
            ],
            "alt": (
                "Archived Ivrit Sheli 2.1.x product tour moving from the responsive "
                "learning dashboard to mobile and Hebrew RTL views; these frames are "
                "not visual proof of the live 2.2.0 interface"
            ),
            "static_alt": (
                "Archived Ivrit Sheli 2.1.x dashboard with adaptive Hebrew learning "
                "and authenticated cloud controls"
            ),
            "mobile_alt": (
                "Archived Ivrit Sheli 2.1.x compact mobile dashboard with focused "
                "learning navigation"
            ),
            "rtl_alt": (
                "Archived Ivrit Sheli 2.1.x Hebrew right-to-left workspace using the "
                "synthetic demo learner"
            ),
            "description": (
                "These pre-2.2 frames document the earlier desktop, mobile and Hebrew "
                "RTL interface. They remain useful interaction history but do not claim "
                "visual proof of the verified live 2.2.0 deployment."
            ),
            "caption": "Archived Ivrit Sheli 2.1.x interface:",
        }
    )
    build_profile._validate_profile_data(updated)
    return updated


def render_outputs(profile: Mapping[str, Any]) -> tuple[str, str]:
    """Render both public README modes from one synchronized profile object."""
    return (
        build_profile.render_profile(profile, "compact"),
        build_profile.render_profile(profile, "expanded"),
    )


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)
    return True


def _load_source(args: argparse.Namespace) -> dict[str, Any]:
    if args.url is not None:
        return fetch_manifest(args.url)
    return load_manifest(args.manifest or args.snapshot)


def prevent_publication_regression(
    reviewed: Mapping[str, Any], incoming: Mapping[str, Any]
) -> None:
    """Reject a same-version remote manifest that loses reviewed publication proof."""
    reviewed_publication = _mapping(reviewed.get("publication"), "reviewed.publication")
    incoming_publication = _mapping(incoming.get("publication"), "incoming.publication")
    if reviewed.get("source_version") != incoming.get("source_version"):
        return
    ranks = {
        "deployment-ahead-of-github-release": 0,
        "published-and-deployed": 1,
    }
    reviewed_rank = ranks.get(reviewed_publication.get("release_state"), -1)
    incoming_rank = ranks.get(incoming_publication.get("release_state"), -1)
    if incoming_rank < reviewed_rank:
        raise ValueError(
            "Remote manifest would regress the reviewed same-version publication state."
        )


def synchronize(args: argparse.Namespace) -> list[Path]:
    """Calculate expected outputs and either write them or return drift paths."""
    manifest = _load_source(args)
    if args.url is not None and args.snapshot.is_file():
        reviewed_snapshot = load_manifest(args.snapshot)
        prevent_publication_regression(reviewed_snapshot, manifest)
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    if not isinstance(profile, dict):
        raise ValueError("Profile JSON root must be an object.")
    expected_profile = apply_manifest(profile, manifest)
    compact, expanded = render_outputs(expected_profile)
    expected = {
        args.snapshot: _canonical_json(manifest),
        args.profile: _canonical_json(expected_profile),
        args.compact_output: compact,
        args.expanded_output: expanded,
    }
    changed: list[Path] = []
    for path, content in expected.items():
        if args.write:
            if _write_if_changed(path, content):
                changed.append(path)
        elif not path.exists() or path.read_text(encoding="utf-8") != content:
            changed.append(path)
    return changed


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        changed = synchronize(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Ivrit Sheli profile sync failed: {error}", file=sys.stderr)
        return 2
    if args.write:
        if changed:
            for path in changed:
                try:
                    display = path.resolve().relative_to(ROOT)
                except ValueError:
                    display = path
                print(f"updated {display}")
        else:
            print("[OK] Ivrit Sheli profile facts are already current.")
        return 0
    if changed:
        print("Ivrit Sheli profile facts are out of date:", file=sys.stderr)
        for path in changed:
            print(f"  - {path}", file=sys.stderr)
        print(
            f"Run: python scripts/sync_ivrit_sheli.py --url {DEFAULT_MANIFEST_URL} --write",
            file=sys.stderr,
        )
        return 1
    print("[OK] Ivrit Sheli profile facts and generated READMEs are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
