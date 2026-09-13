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
EXPECTED_MANIFEST_NAME = "Ivrit Sheli — העברית שלי"
EXPECTED_SCHEMA = "ivrit-sheli-portfolio-project-v3"
EXPECTED_TEST_REPORT = f"{EXPECTED_REPOSITORY}/blob/main/TEST_REPORT.md"
MAX_MANIFEST_BYTES = 512 * 1024
REQUEST_HEADERS = {
    "User-Agent": "Lirioth-profile-sync/3.0",
    "Cache-Control": "no-cache, no-store, max-age=0",
    "Pragma": "no-cache",
}
VERSION_PATTERN = re.compile(r"^[0-9]+(?:\.[0-9]+){2}(?:[-+][0-9A-Za-z.-]+)?$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")

# The upstream manifest already validates its own full contract in IvritSheli's
# CI. Re-implementing all of it here would be two copies of one truth that drift
# apart — which is exactly how this script broke: it pinned the v2 shape and
# stopped reading anything when the project moved to v3.
#
# So this validator checks two things only, and checks them hard:
#   1. Every field the profile actually publishes is present and well formed.
#   2. No published claim outruns what the manifest says it can support.
# Unknown top-level fields are tolerated on purpose, so a future v4 that only
# adds information cannot take the profile offline again. A schema change is
# still refused outright, because that means the fields below may have moved.
CONSUMED_TOP_LEVEL = {
    "schema",
    "slug",
    "name",
    "source_version",
    "source_status",
    "latest_published_release",
    "default_branch",
    "repository_url",
    "durable_demo",
    "summary",
    "languages",
    "standard_stack",
    "tests",
    "historical_deployment",
    "publication",
    "visual_proof",
    "oauth",
    "privacy",
}
DURABLE_DEMO_FIELDS = {"url", "status", "provider", "last_checked_on", "boundary"}
TEST_FIELDS = {
    "version",
    "scope",
    "backend_unique",
    "frontend",
    "frontend_files",
    "total_unique",
    "ordinary_backend_passed",
    "ordinary_backend_skipped",
    "postgresql_gate_passed",
    "evidence",
}
HISTORICAL_FIELDS = {
    "version",
    "provider",
    "former_demo_url",
    "runtime",
    "database",
    "historical_status",
    "release_implementation_commit",
    "verified_on",
    "environment",
    "current_availability",
    "current_http_status",
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
    "readme_screenshot_source_version",
    "readme_screenshot_status",
    "interactive_browser_qa",
}
OAUTH_FIELDS = {
    "providers",
    "source_contract_tested",
    "historical_public_release_version",
    "google_sign_in_verified_at_release",
    "github_successful_session_verified_at_release",
    "authenticated_session_refresh_verified_at_release",
    "onboarding_persistence_across_reload_verified_at_release",
    "logout_verified_at_release",
    "signed_out_reload_verified_at_release",
    "relogin_after_logout_verified_at_release",
    "boundary",
}
PRIVACY_FIELDS = {
    "local_first",
    "demo_data_contract",
    "demo_mutation_contract",
    "durable_demo_currently_available",
    "self_service_export_in_source",
    "self_service_deletion_in_source",
    "contains_secrets",
}
# A demo that is not one of these has a status this script does not know how to
# describe honestly, so it refuses rather than guess a label for the profile.
DEMO_STATUS_LABELS = {
    "verified-live": "live",
    "staging-verified": "staging",
    "unavailable": "unavailable",
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
    """Validate the fields this profile publishes, and their truth boundaries.

    Unknown extra fields are allowed; missing consumed fields are not. See the
    comment above ``CONSUMED_TOP_LEVEL`` for why the split is drawn there.

    Raises:
        ValueError: If a consumed field is missing, malformed, or would let the
            profile publish a claim the manifest does not support.

    Example:
        >>> validate_manifest({})  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ValueError: Unexpected manifest schema.
    """
    _expect(raw.get("schema") == EXPECTED_SCHEMA, "Unexpected manifest schema.")
    _required_keys(raw, CONSUMED_TOP_LEVEL, "manifest")
    _expect(raw.get("slug") == "ivrit-sheli", "Unexpected project slug.")
    _expect(raw.get("name") == EXPECTED_MANIFEST_NAME, "Unexpected project name.")
    _expect(raw.get("default_branch") == "main", "Default branch must be main.")
    _expect(
        raw.get("repository_url") == EXPECTED_REPOSITORY,
        "Unexpected repository URL.",
    )

    source_version = _semantic_version(raw.get("source_version"), "source_version")
    source_status = _plain_text(raw.get("source_status"), "source_status", 40)
    published_release = _release_tag(
        raw.get("latest_published_release"), "latest_published_release"
    )
    _plain_text(raw.get("summary"), "summary", 600)
    languages = _plain_text_list(raw.get("languages"), "languages", 10, 12)
    _expect(set(languages) == {"en", "es", "he"}, "Languages must be en, es and he.")
    stack = _plain_text_list(raw.get("standard_stack"), "standard_stack", 16, 60)
    _expect(len(stack) >= 5, "Standard stack must contain at least five technologies.")

    demo = _mapping(raw.get("durable_demo"), "durable_demo")
    _required_keys(demo, DURABLE_DEMO_FIELDS, "durable_demo")
    demo_status = _plain_text(demo.get("status"), "durable_demo.status", 40)
    _expect(
        demo_status in DEMO_STATUS_LABELS,
        f"Unknown durable_demo.status {demo_status!r}; refusing to label it.",
    )
    demo_url = _plain_text(demo.get("url"), "durable_demo.url", 200)
    _expect(
        demo_url.startswith("https://"),
        "durable_demo.url must be an HTTPS address.",
    )
    _expect(
        ".trycloudflare.com" not in demo_url,
        "durable_demo.url must not be an ephemeral tunnel.",
    )
    _plain_text(demo.get("provider"), "durable_demo.provider", 40)
    _iso_date(demo.get("last_checked_on"), "durable_demo.last_checked_on")
    _plain_text(demo.get("boundary"), "durable_demo.boundary", 1200)

    tests = _mapping(raw.get("tests"), "tests")
    _required_keys(tests, TEST_FIELDS, "tests")
    _expect(
        _semantic_version(tests.get("version"), "tests.version") == source_version,
        "Test evidence version must match source_version.",
    )
    _expect(
        tests.get("scope") == f"{source_status}-local-verification",
        "tests.scope must name the source status it was measured under.",
    )
    backend = _bounded_int(tests.get("backend_unique"), "tests.backend_unique", 1, 100_000)
    frontend = _bounded_int(tests.get("frontend"), "tests.frontend", 1, 100_000)
    total = _bounded_int(tests.get("total_unique"), "tests.total_unique", 1, 200_000)
    _bounded_int(tests.get("frontend_files"), "tests.frontend_files", 1, 10_000)
    _bounded_int(
        tests.get("ordinary_backend_skipped"), "tests.ordinary_backend_skipped", 0, 10_000
    )
    _bounded_int(
        tests.get("postgresql_gate_passed"), "tests.postgresql_gate_passed", 0, 10_000
    )
    _expect(total == backend + frontend, "Total tests must equal backend plus frontend.")
    # The v2 schema counted skipped tests outside backend_unique; v3 counts the
    # passing ones and reports skips separately. This mirrors the rule IvritSheli
    # applies to the same file, rather than inventing a second arithmetic.
    _expect(
        _bounded_int(
            tests.get("ordinary_backend_passed"),
            "tests.ordinary_backend_passed",
            0,
            100_000,
        )
        == backend,
        "Ordinary backend passed must equal backend_unique.",
    )
    _expect(tests.get("evidence") == "TEST_REPORT.md", "Unexpected test evidence path.")

    historical = _mapping(raw.get("historical_deployment"), "historical_deployment")
    _required_keys(historical, HISTORICAL_FIELDS, "historical_deployment")
    _semantic_version(historical.get("version"), "historical_deployment.version")
    commit = _plain_text(
        historical.get("release_implementation_commit"),
        "historical_deployment.release_implementation_commit",
        40,
    )
    _expect(
        bool(COMMIT_PATTERN.fullmatch(commit)),
        "Release implementation commit must be a full SHA-1.",
    )
    _iso_date(historical.get("verified_on"), "historical_deployment.verified_on")
    for field in ("provider", "runtime", "database", "environment", "historical_status"):
        _plain_text(historical.get(field), f"historical_deployment.{field}", 60)
    former = _plain_text(
        historical.get("former_demo_url"), "historical_deployment.former_demo_url", 200
    )
    # This is the defect that sent a recruiter to a 404 for a month: the retired
    # address stayed in the public profile as the live one. It must never be able
    # to come back through this path.
    _expect(
        former != demo_url,
        "The retired deployment URL must not be published as the durable demo.",
    )

    publication = _mapping(raw.get("publication"), "publication")
    _required_keys(publication, PUBLICATION_FIELDS, "publication")
    latest_tag = _release_tag(publication.get("latest_git_tag"), "publication.latest_git_tag")
    latest_release = _release_tag(
        publication.get("latest_github_release"), "publication.latest_github_release"
    )
    tagged = _boolean(publication.get("source_version_tagged"), "publication.source_version_tagged")
    released = _boolean(
        publication.get("source_version_github_release_published"),
        "publication.source_version_github_release_published",
    )
    _plain_text(publication.get("release_state"), "publication.release_state", 120)
    _expect(
        latest_tag == published_release and latest_release == published_release,
        "The published tag and release must agree with latest_published_release.",
    )
    # The whole point of the split between source_version and the published
    # release: a candidate that is not tagged must never be announced as shipped.
    if tagged or released:
        _expect(
            tagged and released and published_release == f"v{source_version}",
            "A source version claimed as tagged or released must be both, at that version.",
        )
    else:
        _expect(
            published_release != f"v{source_version}",
            "An untagged source version must not claim the published release tag.",
        )

    visual = _mapping(raw.get("visual_proof"), "visual_proof")
    _required_keys(visual, VISUAL_PROOF_FIELDS, "visual_proof")
    _plain_text(visual.get("state"), "visual_proof.state", 600)
    _semantic_version(
        visual.get("social_preview_version"), "visual_proof.social_preview_version"
    )
    _semantic_version(
        visual.get("readme_screenshot_source_version"),
        "visual_proof.readme_screenshot_source_version",
    )
    _plain_text(
        visual.get("readme_screenshot_status"), "visual_proof.readme_screenshot_status", 60
    )
    _plain_text(
        visual.get("interactive_browser_qa"), "visual_proof.interactive_browser_qa", 900
    )

    oauth = _mapping(raw.get("oauth"), "oauth")
    _required_keys(oauth, OAUTH_FIELDS, "oauth")
    providers = _plain_text_list(oauth.get("providers"), "oauth.providers", 4, 30)
    _expect(set(providers) == {"Google", "GitHub"}, "OAuth providers must be Google and GitHub.")
    _expect(
        oauth.get("source_contract_tested") is True,
        "oauth.source_contract_tested must be true.",
    )
    _semantic_version(
        oauth.get("historical_public_release_version"),
        "oauth.historical_public_release_version",
    )
    for field in (
        "google_sign_in_verified_at_release",
        "github_successful_session_verified_at_release",
        "authenticated_session_refresh_verified_at_release",
        "onboarding_persistence_across_reload_verified_at_release",
        "logout_verified_at_release",
        "signed_out_reload_verified_at_release",
        "relogin_after_logout_verified_at_release",
    ):
        _boolean(oauth.get(field), f"oauth.{field}")
    _plain_text(oauth.get("boundary"), "oauth.boundary", 600)

    privacy = _mapping(raw.get("privacy"), "privacy")
    _required_keys(privacy, PRIVACY_FIELDS, "privacy")
    _expect(privacy.get("local_first") is True, "Ivrit Sheli must retain a local-first mode.")
    _expect(
        privacy.get("demo_data_contract") == "synthetic", "Public demo data must be synthetic."
    )
    _expect(
        privacy.get("demo_mutation_contract") == "server-blocked",
        "Public demo mutations must be server-blocked.",
    )
    _boolean(
        privacy.get("durable_demo_currently_available"),
        "privacy.durable_demo_currently_available",
    )
    for field in ("self_service_export_in_source", "self_service_deletion_in_source"):
        _expect(privacy.get(field) is True, f"privacy.{field} must be true.")
    _expect(privacy.get("contains_secrets") is False, "Manifest must not contain secrets.")
    # A demo the manifest itself reports as gone must not be linked as reachable.
    if demo_status != "unavailable":
        _expect(
            privacy["durable_demo_currently_available"] is True,
            "A demo published as reachable must be marked currently available.",
        )
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


def _required_keys(value: Mapping[str, Any], expected: set[str], path: str) -> None:
    """Demand every consumed field; tolerate fields this profile does not read.

    Example:
        >>> _required_keys({"a": 1, "b": 2}, {"a"}, "m") is None
        True
    """
    missing = sorted(expected - set(value))
    if missing:
        raise ValueError(f"{path} is missing required fields: {', '.join(missing)}.")


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
    """Return a copy with only the canonical Ivrit project synchronized.

    Every public sentence below is built from manifest values. Nothing about the
    hosting provider, the environment or the demo address is written here, which
    is what let a retired Railway address survive in the published profile for a
    month after the service was gone.
    """
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
    existing_media = copy.deepcopy(project.get("media"))
    tests = validated["tests"]
    demo = validated["durable_demo"]
    historical = validated["historical_deployment"]
    publication = validated["publication"]
    visual = validated["visual_proof"]
    oauth = validated["oauth"]
    privacy = validated["privacy"]
    source_version = validated["source_version"]
    source_status = validated["source_status"]
    published_release = validated["latest_published_release"]
    demo_label = DEMO_STATUS_LABELS[demo["status"]]
    readable_status = source_status.replace("-", " ")

    project["status"] = build_profile.ivrit_status_line(
        source_version, source_status, demo["status"], demo["provider"]
    )
    project["solution"] = validated["summary"]
    project["stack"] = " · ".join(validated["standard_stack"])
    project["demo"] = demo["url"]
    published_clause = (
        f"the published release remains {published_release} while {source_version} is a "
        f"{readable_status}"
        if publication["latest_git_tag"] != f"v{source_version}"
        else f"published as {published_release}"
    )
    project["evidence"] = (
        f"{tests['backend_unique']} backend + {tests['frontend']} frontend = "
        f"{tests['total_unique']} tests on the {source_version} source; "
        f"a {demo_label} demo verified on {demo['last_checked_on']} at "
        f"{demo['provider']}; {published_clause}. "
        f"{oauth['boundary']}"
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
        "source_status": source_status,
        "latest_published_release": published_release,
        "backend_tests": tests["backend_unique"],
        "frontend_tests": tests["frontend"],
        "total_tests": tests["total_unique"],
        "test_scope": tests["scope"],
        "test_report": EXPECTED_TEST_REPORT,
        "demo_url": demo["url"],
        "demo_status": demo["status"],
        "demo_provider": demo["provider"],
        "demo_last_checked_on": demo["last_checked_on"],
        "demo_boundary": demo["boundary"],
        "demo_currently_available": privacy["durable_demo_currently_available"],
        "historical_provider": historical["provider"],
        "historical_version": historical["version"],
        "historical_former_demo_url": historical["former_demo_url"],
        "historical_status": historical["historical_status"],
        "historical_verified_on": historical["verified_on"],
        "release_implementation_commit": historical["release_implementation_commit"],
        "latest_git_tag": publication["latest_git_tag"],
        "latest_github_release": publication["latest_github_release"],
        "source_version_tagged": publication["source_version_tagged"],
        "source_version_github_release_published": publication[
            "source_version_github_release_published"
        ],
        "release_state": publication["release_state"],
        "visual_proof_state": visual["state"],
        "social_preview_version": visual["social_preview_version"],
        "readme_screenshot_source_version": visual["readme_screenshot_source_version"],
        "readme_screenshot_status": visual["readme_screenshot_status"],
        "interactive_browser_qa": visual["interactive_browser_qa"],
        "oauth_providers": oauth["providers"],
        "source_contract_tested": oauth["source_contract_tested"],
        "oauth_historical_release_version": oauth["historical_public_release_version"],
        "google_sign_in_verified_at_release": oauth["google_sign_in_verified_at_release"],
        "github_successful_session_verified_at_release": oauth[
            "github_successful_session_verified_at_release"
        ],
        "authenticated_session_refresh_verified_at_release": oauth[
            "authenticated_session_refresh_verified_at_release"
        ],
        "onboarding_persistence_across_reload_verified_at_release": oauth[
            "onboarding_persistence_across_reload_verified_at_release"
        ],
        "logout_verified_at_release": oauth["logout_verified_at_release"],
        "signed_out_reload_verified_at_release": oauth[
            "signed_out_reload_verified_at_release"
        ],
        "relogin_after_logout_verified_at_release": oauth[
            "relogin_after_logout_verified_at_release"
        ],
        "oauth_boundary": oauth["boundary"],
        "self_service_export_in_source": privacy["self_service_export_in_source"],
        "self_service_deletion_in_source": privacy["self_service_deletion_in_source"],
    }
    if not isinstance(existing_media, dict):
        raise ValueError("Canonical Ivrit Sheli project must retain its media mapping.")
    project["media"] = existing_media
    media = project["media"]
    # v2 could tie media to the commit of the live release. v3 has no commit for
    # the current deployment — only for the retired one — so the honest test left
    # is the version. Frames from an older version are labelled archived, exactly
    # as before, rather than passing as proof of what runs today.
    retain_current_profile_media = (
        existing_media.get("current_release_visual_proof") is True
        and existing_media.get("version") == source_version
    )
    if media.get("current_release_visual_proof") is True and not retain_current_profile_media:
        media.update(
            {
                "current_release_visual_proof": False,
                "alt": (
                    f"Archived Ivrit Sheli {media['version']} product tour captured at "
                    f"runtime build {media['captured_runtime_commit'][:12]}; these frames are "
                    f"not visual proof of the {source_version} source"
                ),
                "static_alt": (
                    f"Archived Ivrit Sheli {media['version']} responsive learning dashboard"
                ),
                "mobile_alt": (
                    f"Archived Ivrit Sheli {media['version']} compact "
                    "mobile learning dashboard"
                ),
                "rtl_alt": (
                    f"Archived Ivrit Sheli {media['version']} Hebrew "
                    "right-to-left workspace"
                ),
                "description": (
                    f"These frames document the deployment captured on "
                    f"{media['captured_on']} and do not claim visual proof of the "
                    f"{source_version} source."
                ),
                "caption": f"Archived Ivrit Sheli {media['version']} interface:",
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


def _demo_rank(manifest: Mapping[str, Any]) -> int:
    """Order demo states so a downgrade can be recognised.

    Example:
        >>> _demo_rank({"durable_demo": {"status": "staging-verified"}})
        1
    """
    demo = manifest.get("durable_demo")
    status = demo.get("status") if isinstance(demo, Mapping) else None
    return {"unavailable": 0, "staging-verified": 1, "verified-live": 2}.get(status, -1)


def prevent_publication_regression(
    reviewed: Mapping[str, Any], incoming: Mapping[str, Any]
) -> None:
    """Reject same-version remote evidence that contradicts reviewed proof.

    A schema change is not a regression, it is a migration, and the two shapes
    are not comparable field by field. In that case the check steps aside and
    says so rather than pretending to have compared them.
    """
    if reviewed.get("schema") != incoming.get("schema"):
        print(
            "Reviewed snapshot uses schema "
            f"{reviewed.get('schema')!r} and the remote manifest uses "
            f"{incoming.get('schema')!r}; the regression check does not apply to a "
            "schema migration and was skipped.",
            file=sys.stderr,
        )
        return
    if reviewed.get("source_version") != incoming.get("source_version"):
        return
    if _demo_rank(incoming) < _demo_rank(reviewed):
        raise ValueError(
            "Remote manifest would downgrade the reviewed same-version demo state."
        )
    reviewed_published = reviewed.get("latest_published_release")
    incoming_published = incoming.get("latest_published_release")
    if reviewed_published != incoming_published:
        raise ValueError(
            "Remote manifest would change the reviewed same-version published release; "
            "publish a new Ivrit semantic version or perform an explicit evidence review."
        )
    reviewed_history = _mapping(
        reviewed.get("historical_deployment"), "reviewed.historical_deployment"
    )
    incoming_history = _mapping(
        incoming.get("historical_deployment"), "incoming.historical_deployment"
    )
    if reviewed_history.get("release_implementation_commit") != incoming_history.get(
        "release_implementation_commit"
    ):
        raise ValueError(
            "Remote manifest would replace the reviewed release implementation commit; "
            "publish a new Ivrit semantic version or perform an explicit evidence review."
        )


def synchronize(args: argparse.Namespace) -> list[Path]:
    """Calculate expected outputs and either write them or return drift paths."""
    manifest = _load_source(args)
    if args.url is not None and args.snapshot.is_file():
        reviewed_snapshot = _decode_object(
            args.snapshot.read_bytes(), str(args.snapshot)
        )
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
