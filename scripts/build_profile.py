"""
Module: GitHub profile builder
Purpose: Generate a recruiter-first compact or expanded README from one JSON source.
Author: Kevin "Lirioth" Cusnir
Date: 2026-07-15 | TZ: Asia/Jerusalem
Notes: Minimal deps; comments in ENGLISH; emojis sparingly.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "profile.json"
DEFAULT_OUTPUT = ROOT / "README.md"

REQUIRED_PROFILE_SECTIONS = {
    "education",
    "evidence_counts",
    "growth",
    "identity",
    "languages",
    "links",
    "profile_version",
    "projects",
    "release",
    "review_path",
    "skills",
    "strengths",
}
IDENTITY_FIELDS = (
    "alias",
    "availability",
    "birthplace",
    "headline",
    "location",
    "name",
    "positioning",
)
LINK_FIELDS = ("cv_en", "cv_es", "cv_he", "email", "github", "linkedin")
PROJECT_FIELDS = (
    "demo",
    "evidence",
    "icon",
    "name",
    "problem",
    "solution",
    "source",
    "stack",
    "status",
)
SKILL_FIELDS = ("backend_data", "frontend", "languages", "quality", "workflow")
LANGUAGE_FIELDS = ("level", "name", "product_value")
EVIDENCE_FIELDS = ("label", "value")
EDUCATION_FIELDS = ("coverage", "current", "period", "program")
REVIEW_PATH_FIELDS = ("action", "evidence", "time")
RELEASE_FIELDS = (
    "baseline",
    "focus",
    "prepared_on",
    "public_data_boundary",
    "status",
    "summary",
    "tag",
    "title",
)
NOVAFIT_SYNC_FIELDS = (
    "asset_count",
    "automated_tests_discovered",
    "live_demo",
    "release_audit",
    "schema",
    "source",
    "theme_count",
    "verification_command",
    "version",
)
NOVAFIT_MEDIA_FIELDS = (
    "alt",
    "animation",
    "caption",
    "description",
    "mobile_static",
    "public_data_boundary",
    "reduced_motion_static",
    "static",
)
IVRIT_RELEASE_EVIDENCE_FIELDS = (
    "backend_tests",
    "frontend_tests",
    "test_report",
    "total_tests",
    "version",
)
IVRIT_SYNC_FIELDS = (
    "authenticated_session_refresh_verified",
    "backend_tests",
    "database",
    "demo_url",
    "dictionary_ready",
    "environment",
    "frontend_tests",
    "health_live",
    "health_ready",
    "latest_git_tag",
    "latest_github_release",
    "live_2_2_interactive_browser_qa",
    "live_version",
    "logout_verified",
    "oauth_boundary",
    "oauth_final_live_code_exchange_verified",
    "postgresql_ready",
    "production_commit",
    "provider",
    "readme_screenshot_version",
    "readme_screenshots_match_live_version",
    "release_state",
    "runtime",
    "schema",
    "social_preview_version",
    "source",
    "source_version",
    "source_version_github_release_published",
    "source_version_tagged",
    "test_report",
    "total_tests",
    "verified_on",
    "visual_proof_state",
)
IVRIT_MEDIA_FIELDS = (
    "alt",
    "animation",
    "captured_on",
    "captured_release_commit",
    "captured_runtime_commit",
    "caption",
    "current_release_visual_proof",
    "description",
    "mobile_alt",
    "mobile_static",
    "public_data_boundary",
    "rtl_alt",
    "rtl_static",
    "static",
    "static_alt",
    "version",
)
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def build_parser() -> argparse.ArgumentParser:
    """Create the profile-builder command-line parser.

    Returns:
        Configured argument parser.

    Raises:
        None.

    Example:
        >>> build_parser().prog
        'build_profile'
    """
    parser = argparse.ArgumentParser(
        prog="build_profile",
        description="Generate an ordered, collapsible GitHub profile README.",
    )
    parser.add_argument(
        "--data", type=Path, default=DEFAULT_DATA, help="Profile JSON source."
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="README destination."
    )
    parser.add_argument(
        "--mode",
        choices=["compact", "expanded"],
        default="compact",
        help="Compact keeps secondary content inside details blocks.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that the output already matches the generated profile without writing it.",
    )
    return parser


def load_profile(path: Path) -> dict[str, Any]:
    """Load and validate profile JSON before rendering.

    Args:
        path: JSON source path.

    Returns:
        Parsed profile mapping.

    Raises:
        FileNotFoundError: If the source does not exist.
        json.JSONDecodeError: If the source is not valid JSON.
        ValueError: If required profile data is absent or malformed.

    Example:
        >>> 'identity' in load_profile(DEFAULT_DATA)
        True
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Profile JSON root must be an object.")
    missing = sorted(REQUIRED_PROFILE_SECTIONS - data.keys())
    if missing:
        raise ValueError(f"Missing profile sections: {', '.join(missing)}")
    _validate_profile_data(data)
    return data


def _validate_profile_data(data: Mapping[str, Any]) -> None:
    """Validate every required field consumed by the renderer."""
    profile_version = _require_semver(data["profile_version"], "profile.profile_version")
    release = _require_mapping(data["release"], "profile.release", RELEASE_FIELDS)
    for field in (
        "baseline",
        "public_data_boundary",
        "status",
        "summary",
        "title",
    ):
        _require_text(release[field], f"profile.release.{field}")
    if release["status"] not in {"release-candidate", "released"}:
        raise ValueError(
            "profile.release.status must be 'release-candidate' or 'released'."
        )
    expected_tag = f"v{profile_version}"
    if release["tag"] != expected_tag:
        raise ValueError(
            f"profile.release.tag must match profile.profile_version as {expected_tag!r}."
        )
    _require_iso_date(release["prepared_on"], "profile.release.prepared_on")
    release_focus = _require_text_list(release["focus"], "profile.release.focus")
    _require_unique(release_focus, "profile.release.focus")

    identity = _require_mapping(data["identity"], "profile.identity", IDENTITY_FIELDS)
    for field in IDENTITY_FIELDS:
        _require_text(identity[field], f"profile.identity.{field}")

    links = _require_mapping(data["links"], "profile.links", LINK_FIELDS)
    for field in LINK_FIELDS:
        path = f"profile.links.{field}"
        if field == "email":
            _require_mailto_url(links[field], path)
        else:
            _require_https_url(links[field], path)

    projects = _require_list(data["projects"], "profile.projects")
    project_names: list[str] = []
    project_urls: list[str] = []
    for index, raw_project in enumerate(projects):
        path = f"profile.projects[{index}]"
        project = _require_mapping(raw_project, path, PROJECT_FIELDS)
        for field in PROJECT_FIELDS:
            if field == "demo" and project[field] is None:
                continue
            field_path = f"{path}.{field}"
            if field in {"source", "demo"}:
                _require_https_url(project[field], field_path)
                project_urls.append(project[field])
            else:
                _require_text(project[field], field_path)
        project_names.append(project["name"])
        if "role_signal" in project:
            _require_text(project["role_signal"], f"{path}.role_signal")
        if "highlights" in project:
            highlights = _require_text_list(
                project["highlights"], f"{path}.highlights", allow_empty=True
            )
            _require_unique(highlights, f"{path}.highlights")

    _require_unique(project_names, "profile.projects names")
    _require_unique(
        project_urls, "profile.projects source/demo URLs", normalize_url=True
    )

    flagship = projects[0]
    if flagship["name"] != "Nova Music Lab":
        raise ValueError(
            "profile.projects must list 'Nova Music Lab' first because the header Live badge "
            "uses the first project's demo URL."
        )
    _require_text(flagship["demo"], "profile.projects[0].demo")

    ivrit_projects = [project for project in projects if project["name"] == "Ivrit Sheli"]
    if len(ivrit_projects) != 1:
        raise ValueError("profile.projects must contain exactly one Ivrit Sheli project.")
    if len(projects) < 2 or projects[1]["name"] != "Ivrit Sheli":
        raise ValueError(
            "profile.projects must list 'Ivrit Sheli' second, directly after Nova Music Lab."
        )
    ivrit = ivrit_projects[0]
    release_evidence = _require_mapping(
        ivrit.get("release_evidence"),
        "profile.projects[Ivrit Sheli].release_evidence",
        IVRIT_RELEASE_EVIDENCE_FIELDS,
    )
    ivrit_version = _require_semver(
        release_evidence["version"],
        "profile.projects[Ivrit Sheli].release_evidence.version",
    )
    for field in ("backend_tests", "frontend_tests", "total_tests"):
        _require_positive_integer(
            release_evidence[field],
            f"profile.projects[Ivrit Sheli].release_evidence.{field}",
        )
    if (
        release_evidence["backend_tests"] + release_evidence["frontend_tests"]
        != release_evidence["total_tests"]
    ):
        raise ValueError(
            "profile.projects[Ivrit Sheli].release_evidence.total_tests must equal "
            "backend_tests + frontend_tests."
        )
    _require_https_url(
        release_evidence["test_report"],
        "profile.projects[Ivrit Sheli].release_evidence.test_report",
    )
    expected_ivrit_status = (
        f"Live v{ivrit_version} dual-mode full-stack product"
        if ivrit["demo"]
        else f"Public v{ivrit_version} full-stack release · live deployment pending"
    )
    if ivrit["status"] != expected_ivrit_status:
        raise ValueError(
            "profile.projects[Ivrit Sheli].status must agree with release_evidence.version "
            "and the presence of a verified live demo URL."
        )
    ivrit_sync = _require_mapping(
        ivrit.get("portfolio_sync"),
        "profile.projects[Ivrit Sheli].portfolio_sync",
        IVRIT_SYNC_FIELDS,
    )
    sync_path = "profile.projects[Ivrit Sheli].portfolio_sync"
    if ivrit_sync["schema"] != "ivrit-sheli-portfolio-project-v1":
        raise ValueError(f"{sync_path}.schema must use the canonical Ivrit contract.")
    if ivrit_sync["source"] != (
        "https://raw.githubusercontent.com/"
        "LiriothTeltanion/IvritSheli/main/portfolio/project.json"
    ):
        raise ValueError(f"{sync_path}.source must use the allow-listed raw manifest URL.")
    sync_source_version = _require_semver(
        ivrit_sync["source_version"], f"{sync_path}.source_version"
    )
    sync_live_version = _require_semver(
        ivrit_sync["live_version"], f"{sync_path}.live_version"
    )
    if sync_source_version != ivrit_version or sync_live_version != ivrit_version:
        raise ValueError(
            f"{sync_path} source/live versions must match release_evidence.version."
        )
    for field in ("backend_tests", "frontend_tests", "total_tests"):
        _require_positive_integer(ivrit_sync[field], f"{sync_path}.{field}")
    if (
        ivrit_sync["backend_tests"] != release_evidence["backend_tests"]
        or ivrit_sync["frontend_tests"] != release_evidence["frontend_tests"]
        or ivrit_sync["total_tests"] != release_evidence["total_tests"]
        or ivrit_sync["test_report"] != release_evidence["test_report"]
    ):
        raise ValueError(f"{sync_path} test evidence must match release_evidence.")
    for field in ("demo_url", "source", "test_report"):
        _require_https_url(ivrit_sync[field], f"{sync_path}.{field}")
    if ivrit_sync["demo_url"] != ivrit["demo"]:
        raise ValueError(f"{sync_path}.demo_url must match the verified project demo URL.")
    if ivrit_sync["test_report"] != (
        "https://github.com/LiriothTeltanion/IvritSheli/blob/main/TEST_REPORT.md"
    ):
        raise ValueError(f"{sync_path}.test_report must use the canonical evidence URL.")
    for field in (
        "database",
        "environment",
        "latest_git_tag",
        "latest_github_release",
        "live_2_2_interactive_browser_qa",
        "oauth_boundary",
        "production_commit",
        "provider",
        "readme_screenshot_version",
        "release_state",
        "runtime",
        "schema",
        "social_preview_version",
        "visual_proof_state",
    ):
        _require_text(ivrit_sync[field], f"{sync_path}.{field}")
    _require_iso_date(ivrit_sync["verified_on"], f"{sync_path}.verified_on")
    if not re.fullmatch(r"[0-9a-f]{40}", ivrit_sync["production_commit"]):
        raise ValueError(f"{sync_path}.production_commit must be a full lowercase SHA-1.")
    if (
        ivrit_sync["provider"] != "Railway"
        or ivrit_sync["runtime"] != "Docker"
        or ivrit_sync["database"] != "PostgreSQL 17"
        or ivrit_sync["environment"] != "production"
    ):
        raise ValueError(f"{sync_path} deployment identity is inconsistent.")
    for field in ("health_live", "health_ready", "postgresql_ready", "dictionary_ready"):
        if _require_boolean(ivrit_sync[field], f"{sync_path}.{field}") is not True:
            raise ValueError(f"{sync_path}.{field} must be true for verified readiness.")
    for field in (
        "source_version_tagged",
        "source_version_github_release_published",
        "readme_screenshots_match_live_version",
        "oauth_final_live_code_exchange_verified",
        "authenticated_session_refresh_verified",
        "logout_verified",
    ):
        _require_boolean(ivrit_sync[field], f"{sync_path}.{field}")
    if ivrit_sync["release_state"] not in {
        "deployment-ahead-of-github-release",
        "published-and-deployed",
    }:
        raise ValueError(f"{sync_path}.release_state is unsupported.")
    for field in ("latest_git_tag", "latest_github_release"):
        tag = ivrit_sync[field]
        if not tag.startswith("v"):
            raise ValueError(f"{sync_path}.{field} must be a v-prefixed semantic version.")
        _require_semver(tag[1:], f"{sync_path}.{field}")
    if ivrit_sync["release_state"] == "deployment-ahead-of-github-release":
        if (
            ivrit_sync["source_version_tagged"] is not False
            or ivrit_sync["source_version_github_release_published"] is not False
        ):
            raise ValueError(
                f"{sync_path} deployment-ahead state cannot claim a current tag or release."
            )
        if any(
            ivrit_sync[field] == f"v{ivrit_version}"
            for field in ("latest_git_tag", "latest_github_release")
        ):
            raise ValueError(f"{sync_path} cannot claim the unpublished source version.")
    elif (
        ivrit_sync["source_version_tagged"] is not True
        or ivrit_sync["source_version_github_release_published"] is not True
        or ivrit_sync["latest_git_tag"] != f"v{ivrit_version}"
        or ivrit_sync["latest_github_release"] != f"v{ivrit_version}"
    ):
        raise ValueError(
            f"{sync_path} published-and-deployed state must match the source version."
        )
    social_preview_version = _require_semver(
        ivrit_sync["social_preview_version"], f"{sync_path}.social_preview_version"
    )
    if social_preview_version != ivrit_version:
        raise ValueError(f"{sync_path}.social_preview_version must match the source version.")
    if ivrit_sync["readme_screenshots_match_live_version"]:
        if (
            ivrit_sync["visual_proof_state"] != "current"
            or ivrit_sync["live_2_2_interactive_browser_qa"] != "verified"
            or ivrit_sync["readme_screenshot_version"] != ivrit_sync["live_version"]
        ):
            raise ValueError(
                f"{sync_path} current upstream screenshots require matching live-version "
                "media and verified browser QA."
            )
    elif (
        ivrit_sync["visual_proof_state"] != "partial"
        or ivrit_sync["live_2_2_interactive_browser_qa"] != "pending"
    ):
        raise ValueError(
            f"{sync_path} stale upstream screenshots require the partial/pending boundary."
        )
    if not re.fullmatch(
        r"[0-9]+\.[0-9]+\.(?:[0-9]+|x)",
        ivrit_sync["readme_screenshot_version"],
    ):
        raise ValueError(f"{sync_path}.readme_screenshot_version is invalid.")
    if (
        ivrit_sync["oauth_final_live_code_exchange_verified"] is not False
        or ivrit_sync["authenticated_session_refresh_verified"] is not False
        or ivrit_sync["logout_verified"] is not False
    ):
        raise ValueError(
            f"{sync_path} OAuth exchange, session refresh and logout must remain unverified."
        )
    ivrit_media = _require_mapping(
        ivrit.get("media"),
        "profile.projects[Ivrit Sheli].media",
        IVRIT_MEDIA_FIELDS,
    )
    for field in (
        "alt",
        "caption",
        "captured_release_commit",
        "captured_runtime_commit",
        "description",
        "mobile_alt",
        "public_data_boundary",
        "rtl_alt",
        "static_alt",
        "version",
    ):
        _require_text(ivrit_media[field], f"profile.projects[Ivrit Sheli].media.{field}")
    _require_iso_date(
        ivrit_media["captured_on"],
        "profile.projects[Ivrit Sheli].media.captured_on",
    )
    for field in ("captured_release_commit", "captured_runtime_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", ivrit_media[field]):
            raise ValueError(
                f"profile.projects[Ivrit Sheli].media.{field} must be a full "
                "lowercase SHA-1."
            )
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.(?:[0-9]+|x)", ivrit_media["version"]):
        raise ValueError(
            "profile.projects[Ivrit Sheli].media.version must be a semantic version "
            "or x patch series."
        )
    _require_boolean(
        ivrit_media["current_release_visual_proof"],
        "profile.projects[Ivrit Sheli].media.current_release_visual_proof",
    )
    if ivrit_media["current_release_visual_proof"]:
        if ivrit_media["version"] != ivrit_sync["live_version"]:
            raise ValueError(
                "Current profile-owned Ivrit media must match the verified live version."
            )
        if ivrit_media["captured_release_commit"] != ivrit_sync["production_commit"]:
            raise ValueError(
                "Current profile-owned Ivrit media must match the verified release baseline."
            )
    for field in ("animation", "mobile_static", "rtl_static", "static"):
        _require_asset_path(
            ivrit_media[field], f"profile.projects[Ivrit Sheli].media.{field}"
        )
    if len(
        {
            ivrit_media["animation"],
            ivrit_media["mobile_static"],
            ivrit_media["rtl_static"],
            ivrit_media["static"],
        }
    ) != 4:
        raise ValueError(
            "profile.projects[Ivrit Sheli].media must use distinct animation, desktop, "
            "mobile and RTL assets."
        )

    novafit_projects = [project for project in projects if project["name"] == "NovaFit"]
    if len(novafit_projects) != 1:
        raise ValueError("profile.projects must contain exactly one NovaFit project.")
    novafit = novafit_projects[0]
    sync = _require_mapping(
        novafit.get("portfolio_sync"),
        "profile.projects[NovaFit].portfolio_sync",
        NOVAFIT_SYNC_FIELDS,
    )
    novafit_version = _require_semver(
        sync["version"], "profile.projects[NovaFit].portfolio_sync.version"
    )
    for field in ("asset_count", "automated_tests_discovered", "theme_count"):
        _require_positive_integer(
            sync[field], f"profile.projects[NovaFit].portfolio_sync.{field}"
        )
    for field in ("release_audit", "schema", "verification_command"):
        _require_text(sync[field], f"profile.projects[NovaFit].portfolio_sync.{field}")
    for field in ("live_demo", "source"):
        _require_https_url(sync[field], f"profile.projects[NovaFit].portfolio_sync.{field}")
    if sync["live_demo"] != novafit["demo"]:
        raise ValueError(
            "profile.projects[NovaFit].portfolio_sync.live_demo must match the NovaFit demo URL."
        )
    expected_status = f"Active v{novafit_version} local-first desktop product"
    if novafit["status"] != expected_status:
        raise ValueError(
            "profile.projects[NovaFit].status must agree with portfolio_sync.version."
        )

    media = _require_mapping(
        novafit.get("media"),
        "profile.projects[NovaFit].media",
        NOVAFIT_MEDIA_FIELDS,
    )
    for field in ("alt", "caption", "description", "public_data_boundary"):
        _require_text(media[field], f"profile.projects[NovaFit].media.{field}")
    for field in ("animation", "mobile_static", "reduced_motion_static", "static"):
        _require_asset_path(media[field], f"profile.projects[NovaFit].media.{field}")
    if media["mobile_static"] != media["static"]:
        raise ValueError(
            "profile.projects[NovaFit].media.mobile_static must use the canonical static fallback."
        )
    if media["reduced_motion_static"] != media["static"]:
        raise ValueError(
            "profile.projects[NovaFit].media.reduced_motion_static must use the canonical static fallback."
        )

    skills = _require_mapping(data["skills"], "profile.skills", SKILL_FIELDS)
    all_skills: list[str] = []
    for field in SKILL_FIELDS:
        items = _require_text_list(skills[field], f"profile.skills.{field}")
        _require_unique(items, f"profile.skills.{field}")
        all_skills.extend(items)
    _require_unique(all_skills, "profile.skills across categories")

    languages = _require_list(data["languages"], "profile.languages")
    language_names: list[str] = []
    for index, raw_language in enumerate(languages):
        path = f"profile.languages[{index}]"
        language = _require_mapping(raw_language, path, LANGUAGE_FIELDS)
        for field in LANGUAGE_FIELDS:
            _require_text(language[field], f"{path}.{field}")
        language_names.append(language["name"])
    _require_unique(language_names, "profile.languages names")

    evidence_counts = _require_list(data["evidence_counts"], "profile.evidence_counts")
    evidence_labels: list[str] = []
    for index, raw_item in enumerate(evidence_counts):
        path = f"profile.evidence_counts[{index}]"
        item = _require_mapping(raw_item, path, EVIDENCE_FIELDS)
        _require_text(item["label"], f"{path}.label")
        if (
            not isinstance(item["value"], int)
            or isinstance(item["value"], bool)
            or item["value"] < 0
        ):
            raise ValueError(f"{path}.value must be a non-negative integer.")
        evidence_labels.append(item["label"])
    _require_unique(evidence_labels, "profile.evidence_counts labels")

    strengths = _require_text_list(data["strengths"], "profile.strengths")
    growth = _require_text_list(data["growth"], "profile.growth")
    _require_unique(strengths, "profile.strengths")
    _require_unique(growth, "profile.growth")

    education = _require_mapping(
        data["education"], "profile.education", EDUCATION_FIELDS
    )
    for field in EDUCATION_FIELDS:
        _require_text(education[field], f"profile.education.{field}")

    review_path = _require_list(data["review_path"], "profile.review_path")
    review_times: list[str] = []
    for index, raw_item in enumerate(review_path):
        path = f"profile.review_path[{index}]"
        item = _require_mapping(raw_item, path, REVIEW_PATH_FIELDS)
        for field in REVIEW_PATH_FIELDS:
            _require_text(item[field], f"{path}.{field}")
        review_times.append(item["time"])
    _require_unique(review_times, "profile.review_path times")


def _require_mapping(
    value: Any,
    path: str,
    required_fields: Sequence[str],
) -> Mapping[str, Any]:
    """Return an object after checking its type and required keys."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object.")
    missing = sorted(field for field in required_fields if field not in value)
    if missing:
        raise ValueError(f"Missing required fields in {path}: {', '.join(missing)}")
    return value


def _require_list(value: Any, path: str, *, allow_empty: bool = False) -> list[Any]:
    """Return a JSON array after checking its type and minimum size."""
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array.")
    if not value and not allow_empty:
        raise ValueError(f"{path} must contain at least one item.")
    return value


def _require_text(value: Any, path: str) -> str:
    """Return non-empty text or raise an actionable validation error."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty string.")
    return value


def _require_semver(value: Any, path: str) -> str:
    """Return a strict Semantic Versioning 2.0 value."""
    version = _require_text(value, path)
    if not SEMVER_PATTERN.fullmatch(version):
        raise ValueError(f"{path} must be a Semantic Versioning value such as 2.0.0.")
    return version


def _require_iso_date(value: Any, path: str) -> str:
    """Return an ISO 8601 calendar date after strict parsing."""
    raw = _require_text(value, path)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        raise ValueError(f"{path} must be an ISO date in YYYY-MM-DD format.")
    try:
        date.fromisoformat(raw)
    except ValueError as error:
        raise ValueError(f"{path} must be an ISO date in YYYY-MM-DD format.") from error
    return raw


def _require_positive_integer(value: Any, path: str) -> int:
    """Return a positive integer while rejecting booleans."""
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{path} must be a positive integer.")
    return value


def _require_boolean(value: Any, path: str) -> bool:
    """Return a JSON boolean while rejecting truthy strings and integers."""
    if not isinstance(value, bool):
        raise ValueError(f"{path} must be boolean.")
    return value


def _require_asset_path(value: Any, path: str) -> str:
    """Validate a repository-relative public asset path."""
    asset = _require_text(value, path)
    parts = asset.split("/")
    parsed = urlsplit(asset)
    if (
        not asset.startswith("assets/")
        or "\\" in asset
        or any(part in {"", ".", ".."} for part in parts)
        or parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{path} must be a clean repository-relative assets/ path.")
    return asset


def _require_text_list(
    value: Any, path: str, *, allow_empty: bool = False
) -> list[Any]:
    """Validate an array containing only non-empty strings."""
    items = _require_list(value, path, allow_empty=allow_empty)
    for index, item in enumerate(items):
        _require_text(item, f"{path}[{index}]")
    return items


def _require_https_url(value: Any, path: str) -> str:
    """Validate a public HTTPS URL without embedded credentials."""
    url = _require_text(value, path)
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or any(character.isspace() for character in url)
    ):
        raise ValueError(f"{path} must be an absolute HTTPS URL without credentials.")
    return url


def _require_mailto_url(value: Any, path: str) -> str:
    """Validate the public contact email as a simple mailto URL."""
    url = _require_text(value, path)
    parsed = urlsplit(url)
    address = parsed.path
    if (
        parsed.scheme != "mailto"
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or address.count("@") != 1
        or address.startswith("@")
        or address.endswith("@")
        or any(character.isspace() for character in address)
    ):
        raise ValueError(f"{path} must be a simple mailto URL.")
    return url


def _require_unique(
    values: Sequence[str],
    path: str,
    *,
    normalize_url: bool = False,
) -> None:
    """Reject case-insensitive duplicate labels or equivalent URLs."""
    seen: dict[str, str] = {}
    for value in values:
        if normalize_url:
            parsed = urlsplit(value)
            key = parsed._replace(
                scheme=parsed.scheme.lower(),
                netloc=parsed.netloc.lower(),
                path=parsed.path.rstrip("/"),
            ).geturl()
        else:
            key = value.strip().casefold()
        if key in seen:
            raise ValueError(
                f"{path} contains duplicate values: {seen[key]!r} and {value!r}."
            )
        seen[key] = value


def render_profile(data: Mapping[str, Any], mode: str = "compact") -> str:
    """Render the complete recruiter-facing Markdown profile.

    Args:
        data: Validated profile data.
        mode: ``compact`` or ``expanded``.

    Returns:
        UTF-8 Markdown text ending in one newline.

    Raises:
        ValueError: If the mode is unsupported.

    Example:
        >>> '# Kevin Cusnir' in render_profile(load_profile(DEFAULT_DATA))
        True
    """
    if mode not in {"compact", "expanded"}:
        raise ValueError("Mode must be compact or expanded.")

    identity = data["identity"]
    links = data["links"]
    profile_version = data["profile_version"]
    projects = data["projects"]
    release = data["release"]
    review_path = data["review_path"]
    skills = data["skills"]
    novafit = next(project for project in projects if project["name"] == "NovaFit")
    ivrit = next(project for project in projects if project["name"] == "Ivrit Sheli")
    ivrit_header_url = ivrit.get("demo") or ivrit["source"]
    ivrit_header_label = "א Ivrit Sheli live" if ivrit.get("demo") else "א Ivrit Sheli"
    novafit_sync = novafit["portfolio_sync"]
    novafit_version = novafit_sync["version"]
    fast_review = " · ".join(
        f"**{item['time']}**: {item['action']}" for item in review_path
    )

    lines: list[str] = [
        (
            f"<!-- profile-version: {profile_version}; release-tag: {release['tag']}; "
            f"release-title: {release['title']} -->"
        ),
        "",
        '<a id="top"></a>',
        '<div align="center">',
        "",
        "<picture>",
        '  <source media="(max-width: 640px) and (prefers-reduced-motion: reduce)" srcset="./assets/profile-banner-mobile-static.svg" />',
        '  <source media="(max-width: 640px)" srcset="./assets/profile-banner-mobile-animated.svg" />',
        '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/profile-banner-static.svg" />',
        '  <img src="./assets/profile-banner-animated.svg" width="100%" alt="Portrait of Kevin Cusnir with the Lirioth Teltanion creative identity, KC star LT signature and frontend, full-stack and creative engineering focus" />',
        "</picture>",
        "",
        f"# {identity['name']} · {identity['alias']} ✨",
        "",
        f"<p><strong>{identity['headline']}</strong></p>",
        "",
        f"**{identity['positioning']}**",
        "",
        f"[💼 LinkedIn]({links['linkedin']}) · [📄 CV EN]({links['cv_en']}) · [CV ES]({links['cv_es']}) · [CV HE]({links['cv_he']}) · [✉️ Email]({links['email']}) · [🎧 Nova Music Lab live]({projects[0]['demo']}) · [{ivrit_header_label}]({ivrit_header_url})",
        "",
        f"**Open to:** Junior Frontend & Full-Stack roles · **Born in:** {identity['birthplace']} · **Based in:** {identity['location']} · **Languages:** ES · EN · HE",
        "",
        "[Read in English](./README.md) · [Leer en español](./PROFILE_ES.md) · [עברית](./PROFILE_HE.md)",
        "",
        "[Snapshot](#-recruiter-snapshot) · [Projects](#-featured-projects) · [Evidence](#-engineering-evidence) · [Global](#-global-communication) · [Contact](#-contact)",
        "",
        "</div>",
        "",
        "---",
        "",
        "## ⚡ Recruiter snapshot",
        "",
        f"I’m **{identity['name']}**, born in **{identity['birthplace']}** and now based in **{identity['location']}**. {identity['positioning']}",
        "",
        f"> **{identity['availability']}.** Best fit: a junior team with mentorship, real users, thoughtful review and room for structured creativity.",
        "",
        "| What I can prove publicly | Strongest evidence |",
        "|---|---|",
        "| React and TypeScript product work | Nova Music Lab, Ivrit Sheli and Christopher Rodríguez Portfolio |",
        f"| Full-stack, Python and data persistence | Ivrit Sheli v{ivrit['release_evidence']['version']} with FastAPI/PostgreSQL; NovaFit v{novafit_version} with Python/SQLite |",
        "| Data, accessibility and multilingual UX | Honest source-aware analytics; EN/ES/HE, RTL, keyboard and reduced-motion work |",
        f"| Delivery discipline | {ivrit['release_evidence']['total_tests']}-test full-stack proof, Docker, CI, live deployments, bundle budgets and release checks |",
        "",
        f"**Review path:** {fast_review}.",
        "",
        "---",
        "",
        "## 🚀 Featured projects",
        "",
    ]

    for project in projects:
        lines.extend(_render_project(project))
        if project["name"] == "Nova Music Lab":
            lines.extend(_render_nova_music_spotlight(project))
        elif project["name"] == "Ivrit Sheli":
            lines.extend(_render_ivrit_spotlight(project))
        elif project["name"] == "NovaFit":
            lines.extend(_render_novafit_spotlights(project))

    lines.extend(
        [
            "---",
            "",
            "## 🧪 Engineering evidence",
            "",
            "<picture>",
            '  <source media="(max-width: 640px) and (prefers-reduced-motion: reduce)" srcset="./assets/engineering-orbit-mobile-static.svg" />',
            '  <source media="(max-width: 640px)" srcset="./assets/engineering-orbit-mobile.svg" />',
            '  <img src="./assets/engineering-orbit-animated.svg" width="100%" alt="Product engineering connects frontend, Python, data, accessibility, privacy, testing and delivery" />',
            "</picture>",
            "",
            "> Evidence counts come from the featured public projects and their documented quality pipelines.",
            "",
            "| Evidence across featured work | Count |",
            "|---|---:|",
        ]
    )
    for item in data["evidence_counts"]:
        lines.append(f"| {item['label']} | **{item['value']}** |")

    lines.extend(
        [
            "",
            "### Core stack",
            "",
            f"**Languages:** {_join(skills['languages'])}<br>",
            f"**Frontend:** {_join(skills['frontend'])}<br>",
            f"**Backend & data:** {_join(skills['backend_data'])}<br>",
            f"**Testing & quality:** {_join(skills['quality'])}<br>",
            f"**Workflow:** {_join(skills['workflow'])}",
            "",
            "---",
            "",
            "## 🌍 Global communication",
            "",
            f"**Life route:** {identity['birthplace']} → {identity['location']}",
            "",
            "Country boundaries and deterministic tiny-state markers represent 195 sovereign states while framing a personal journey from Venezuelan roots to an Israeli home, supported by Spanish, English and Hebrew communication.",
            "",
            "<picture>",
            '  <source media="(max-width: 640px) and (prefers-reduced-motion: reduce)" srcset="./assets/world-globe-mobile-static.svg" />',
            '  <source media="(max-width: 640px)" srcset="./assets/world-globe-mobile.svg" />',
            '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/world-globe-static.svg" />',
            '  <img src="./assets/world-globe-animated.svg" width="100%" alt="World map with country boundaries marking Kevin Cusnir’s birthplace in San Cristóbal, Venezuela and current base in Beersheba, Israel" />',
            "</picture>",
            "",
            "| Language | Level | Product value |",
            "|---|---|---|",
        ]
    )
    for language in data["languages"]:
        lines.append(
            f"| **{language['name']}** | {language['level']} | {language['product_value']} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 🌱 Current growth focus",
            "",
            "<picture>",
            '  <source media="(max-width: 640px)" srcset="./assets/learning-roadmap-mobile.svg" />',
            '  <img src="./assets/learning-roadmap-animated.svg" width="100%" alt="Roadmap from proven frontend work through data and application trust to production full-stack delivery" />',
            "</picture>",
            "",
        ]
    )
    lines.append(f"**Next depth:** {_join(data['growth'])}")

    lines.extend(
        [
            "",
            "---",
            "",
        ]
    )

    secondary = _render_secondary(data)
    if mode == "compact":
        lines.extend(
            [
                "<details>",
                "<summary><strong>🧠 Engineering approach and transferable strengths</strong></summary>",
                "",
                *secondary["approach"],
                "",
                "</details>",
                "",
                "<details>",
                "<summary><strong>🎓 Education and structured learning</strong></summary>",
                "",
                *secondary["education"],
                "",
                "</details>",
                "",
                "<details>",
                "<summary><strong>🧙‍♂️ Kevin and Lirioth — professional structure and creative signature</strong></summary>",
                "",
                *secondary["identity"],
                "",
                "</details>",
            ]
        )
    else:
        lines.extend(
            [
                "## 🧠 Engineering approach and strengths",
                "",
                *secondary["approach"],
                "",
                "## 🎓 Education and structured learning",
                "",
                *secondary["education"],
                "",
                "## 🧙‍♂️ Kevin and Lirioth",
                "",
                *secondary["identity"],
            ]
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 🤝 Contact",
            "",
            f"- 💼 [LinkedIn — {identity['name']}]({links['linkedin']})",
            f"- 📄 [English CV]({links['cv_en']}) · [Currículum en español]({links['cv_es']}) · [קורות חיים בעברית]({links['cv_he']})",
            f"- 🐙 [GitHub — {identity['alias']}]({links['github']})",
            f"- ✉️ [Email Kevin]({links['email']})",
            "",
            '<p align="right"><a href="#top">⬆️ Back to top</a></p>',
            "",
            '<div align="center">',
            "",
            "<picture>",
            '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/brand/kc-lt-signature.svg" />',
            '  <img src="./assets/brand/kc-lt-signature-animated.svg" width="360" alt="KC star LT handwritten blue signature, the personal mark of Kevin Cusnir and Lirioth Teltanion" />',
            "</picture>",
            "",
            "**Code with purpose. Design with personality. Data with honesty.** 💙",
            "",
            "</div>",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_profile(data_path: Path, output_path: Path, mode: str) -> Path:
    """Generate and atomically write a profile README.

    Args:
        data_path: JSON source.
        output_path: Markdown destination.
        mode: Compact or expanded rendering mode.

    Returns:
        Written output path.

    Raises:
        OSError: If the output cannot be written.
        ValueError: If source data is incomplete.

    Example:
        >>> write_profile(DEFAULT_DATA, ROOT / 'README.preview.md', 'compact').suffix  # doctest: +SKIP
        '.md'
    """
    content = render_profile(load_profile(data_path), mode)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    # Markdown is committed with LF via .gitattributes. Force the same output on
    # Windows so generated-file checks do not report CRLF-only drift.
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(output_path)
    return output_path


def _render_project(project: Mapping[str, Any]) -> list[str]:
    project_name = project["name"]
    links = [f"[{project_name} source]({project['source']})"]
    if project.get("demo"):
        links.insert(0, f"[Open {project_name} live demo]({project['demo']})")
    return [
        f"### {project['icon']} {project['name']}",
        "",
        f"**Status:** {project['status']} · **Stack:** {project['stack']}<br>",
        f"**Problem → solution:** {project['problem']} {project['solution']}<br>",
        f"**Evidence:** {project['evidence']} · **Role signal:** {project.get('role_signal', 'Product engineering')}<br>",
        " · ".join(links),
        "",
    ]


def _render_nova_music_spotlight(project: Mapping[str, Any]) -> list[str]:
    """Render the live flagship preview and its data journey."""
    return [
        f'<a href="{project["demo"]}">',
        "<picture>",
        '  <source media="(max-width: 640px)" srcset="./assets/nova-music-live-preview-mobile.jpg" />',
        '  <img src="./assets/nova-music-live-preview.jpg" width="100%" alt="Current Nova Music Lab hero showing the bundled demonstration museum, navigation and live product calls to action" />',
        "</picture>",
        "</a>",
        "",
        "**Live product preview:** responsive React interface, bundled demonstration museum and a direct path to the working deployment.",
        "",
        "<details>",
        "<summary><strong>🎧 Open the Nova Music Lab data journey</strong></summary>",
        "",
        "<picture>",
        '  <source media="(max-width: 640px) and (prefers-reduced-motion: reduce)" srcset="./assets/nova-music-journey-mobile-static.svg" />',
        '  <source media="(max-width: 640px)" srcset="./assets/nova-music-journey-mobile.svg" />',
        '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/nova-music-journey-static.svg" />',
        '  <img src="./assets/nova-music-journey-animated.svg" width="100%" alt="Private listening files move through normalization, analytics, emotion mapping and identity into an exportable museum report" />',
        "</picture>",
        "",
        "Five import families become one deduplicated, source-aware listening history. Missing fields remain visible as gaps, and raw exports stay in the browser.",
        "",
        f"[Explore the live music museum]({project['demo']}) · [Inspect the Nova Music Lab source]({project['source']})",
        "",
        "</details>",
        "",
    ]


def _render_ivrit_spotlight(project: Mapping[str, Any]) -> list[str]:
    """Render current engineering proof beside honestly versioned visual media."""

    media = project["media"]
    evidence = project["release_evidence"]
    sync = project["portfolio_sync"]
    live_link = (
        f' · <a href="{project["demo"]}">Open verified live deployment</a>'
        if project.get("demo")
        else " · <strong>Live deployment pending:</strong> source and local/Docker paths are public now."
    )
    publication_text = (
        f"the verified deployment, Git tag and GitHub Release now agree on "
        f"v{sync['live_version']}."
        if sync["release_state"] == "published-and-deployed"
        else (
            f"the verified deployment runs v{sync['live_version']}; the latest Git "
            f"tag and GitHub release remain {sync['latest_git_tag']} while the "
            "current release package is pending."
        )
    )
    if media["current_release_visual_proof"]:
        summary = (
            f"א Open the current Ivrit Sheli {media['version']} product tour and "
            f"verified full-stack proof"
        )
        visual_boundary = (
            f"These profile-owned captures passed fresh desktop, mobile and Hebrew RTL "
            f"browser QA on {media['captured_on']} against the live {sync['live_version']} "
            f"interface at runtime build {media['captured_runtime_commit'][:12]}, using "
            f"release baseline {media['captured_release_commit'][:12]}. The upstream "
            "project manifest remains independently review-gated."
        )
        rtl_label = "Open the current Hebrew RTL frame"
    else:
        summary = (
            f"א Open the archived Ivrit Sheli {media['version']} product tour and "
            f"verified {evidence['version']} full-stack proof"
        )
        visual_boundary = (
            f"These {media['version']} screens are interaction history, not visual proof "
            f"of the live {sync['live_version']} interface."
        )
        rtl_label = "Open the archived Hebrew RTL frame"
    return [
        "<details>",
        f"<summary><strong>{summary}</strong></summary>",
        f"<p><strong>Public-data boundary:</strong> {media['public_data_boundary']}</p>",
        f"<p><strong>Visual evidence boundary:</strong> {visual_boundary}</p>",
        "<picture>",
        f'  <source media="(max-width: 640px) and (prefers-reduced-motion: reduce)" srcset="./{media["mobile_static"]}" />',
        f'  <source media="(max-width: 640px)" srcset="./{media["mobile_static"]}" />',
        f'  <source media="(prefers-reduced-motion: reduce)" srcset="./{media["static"]}" />',
        f'  <img src="./{media["animation"]}" width="100%" alt="{media["alt"]}" />',
        "</picture>",
        f"<p><strong>{media['caption']}</strong> {media['description']}</p>",
        (
            f"<p><strong>Verified v{evidence['version']} evidence:</strong> {evidence['backend_tests']} backend + "
            f"{evidence['frontend_tests']} frontend = {evidence['total_tests']} passing tests · "
            f"Railway {sync['environment']} · {sync['database']} ready · live/ready health "
            f"checks true · production commit <code>{sync['production_commit'][:12]}</code> · "
            "tenant RLS · Alembic · non-root Docker · redacted structured JSON logs.</p>"
        ),
        (
            f"<p><strong>OAuth boundary:</strong> {sync['oauth_boundary']}</p>"
        ),
        (
            f"<p><strong>Publication boundary:</strong> {publication_text}</p>"
        ),
        f'<p><a href="{project["source"]}">Inspect the Ivrit Sheli source</a> · <a href="{evidence["test_report"]}">Review the test contract</a> · <a href="./data/project-snapshots/ivrit-sheli.json">Inspect the reviewed upstream project snapshot</a> · <a href="./{media["rtl_static"]}">{rtl_label}</a>{live_link}</p>',
        "</details>",
        "",
    ]


def _render_novafit_spotlights(project: Mapping[str, Any]) -> list[str]:
    """Render two focused NovaFit tours while keeping the main project list scannable."""
    sync = project["portfolio_sync"]
    media = project["media"]
    version = sync["version"]
    release_tag = f"v{version}"
    release_url = f"{project['source']}/releases/tag/{release_tag}"
    test_count = sync["automated_tests_discovered"]
    theme_count = sync["theme_count"]
    asset_count = sync["asset_count"]
    verification = sync["verification_command"]
    release_audit = sync["release_audit"]
    manifest_source = sync["source"]
    live_demo = project["demo"]
    return [
        "<details>",
        (
            f"<summary><strong>💙 Open the NovaFit {version} product tour and "
            "verified evidence</strong></summary>"
        ),
        "",
        f"> **Public-data boundary:** {media['public_data_boundary']}",
        "",
        "<picture>",
        (
            '  <source media="(max-width: 640px) and '
            '(prefers-reduced-motion: reduce)" '
            f'srcset="./{media["mobile_static"]}" />'
        ),
        f'  <source media="(max-width: 640px)" srcset="./{media["mobile_static"]}" />',
        f'  <source media="(prefers-reduced-motion: reduce)" srcset="./{media["reduced_motion_static"]}" />',
        f'  <img src="./{media["animation"]}" width="100%" alt="{media["alt"]}" />',
        "</picture>",
        "",
        f"**{media['caption']}** {media['description']}",
        "",
        f"**Manifest-backed product summary:** {project['solution']}",
        "",
        (
            f"**Verified {release_tag} evidence:** {test_count} discovered automated "
            f"tests · {theme_count} themes · {asset_count} public visual assets · "
            "EN/ES/HE with Hebrew RTL · complete verified backups · installable "
            "static showcase · one-click Windows release."
        ),
        "",
        '<a href="./assets/analytics-training-atlas.png"><img src="./assets/analytics-training-atlas.png" width="100%" alt="NovaFit Training Atlas workspace showing seeded analytical charts" /></a>',
        "",
        '<a href="./assets/theme-spectrum.png"><img src="./assets/theme-spectrum.png" width="100%" alt="NovaFit twelve-theme interface contact sheet" /></a>',
        "",
        "The Training Atlas is profile-independent; the theme contact sheet uses seeded demonstration records without publishing a profile name.",
        "",
        f"**{theme_count} curated themes:** Midnight Neon · Aurora Borealis · Negev Sunrise · Ocean Depth · Forest Focus · Rose Quartz · Cloud Day · Solar Paper · High Contrast · Royal Sapphire · Cyber Lime · Sunset Arcade.",
        "",
        (
            f"[Open the NovaFit live showcase]({live_demo}) · "
            f"[Download the verified {release_tag} release]({release_url}) · "
            f"[Inspect the NovaFit source]({project['source']}) · "
            f"[Verified project manifest]({manifest_source})"
        ),
        "",
        "</details>",
        "",
        "<details>",
        "<summary><strong>🌍 Open NovaFit profiles, EN/ES/HE, coach and safe delivery</strong></summary>",
        "",
        "> **Public-data boundary:** this system map contains no profile names, dates or wellness metrics.",
        "",
        "<picture>",
        '  <source media="(max-width: 640px)" srcset="./assets/novafit-trust-system-mobile.svg" />',
        '  <img src="./assets/novafit-trust-system-animated.svg" width="100%" alt="NovaFit protects profile boundaries, checks data quality, explains conservative suggestions, verifies the workspace and stages clean releases" />',
        "</picture>",
        "",
        "Each profile owns isolated records, goals, language, theme and activity preferences. English and Spanish use LTR; Hebrew moves the shell to RTL. Suggestions expose data confidence and reasons while avoiding medical claims.",
        "",
        f"The checker repairs a local `.venv`, validates Matplotlib and `Asia/Jerusalem`, runs {test_count} discovered automated tests, preserves an existing user database in workspace mode, and uses `{verification}` plus `{release_audit}` for reproducible verification and clean downloadable releases.",
        "",
        "</details>",
        "",
    ]


def _render_secondary(data: Mapping[str, Any]) -> dict[str, list[str]]:
    education = data["education"]
    approach = [
        "### What I bring to a team",
        "",
        *[f"- {item}" for item in data["strengths"]],
        "",
        "### Working principles",
        "",
        "- Make the user-facing claim proportional to the evidence.",
        "- Keep inputs validated and failure states actionable.",
        "- Treat accessibility, privacy and documentation as implementation work.",
        "- Prefer small reversible changes, focused commits and reproducible checks.",
        "- Use AI to accelerate review and exploration without outsourcing understanding.",
    ]
    education_lines = [
        f"**{education['program']}**  ",
        f"{education['period']}  ",
        f"**Coverage:** {education['coverage']}  ",
        f"**Current status:** {education['current']}",
        "",
        "The public learning archive remains separate from production-ready projects so recruiters can distinguish progression from finished product evidence.",
    ]
    identity_lines = [
        "**Kevin** is the professional engineering identity: implementation, debugging, documentation, responsibility and collaboration.",
        "",
        "**Lirioth Teltanion** is the creative signature: music technology, visual language, narrative systems, experimental interfaces and generative art.",
        "",
        "Together, these identities make technically sound products easier to understand, remember and enjoy.",
    ]
    return {
        "approach": approach,
        "education": education_lines,
        "identity": identity_lines,
    }


def _join(values: Sequence[str]) -> str:
    return " · ".join(values)


def main() -> int:
    """Generate the selected profile mode.

    Returns:
        ``0`` after writing the README.

    Raises:
        Exception: Source or file errors remain visible to the developer.

    Example:
        >>> main()  # doctest: +SKIP
        0
    """
    args = build_parser().parse_args()
    if args.check:
        expected = render_profile(load_profile(args.data), args.mode)
        if not args.output.exists():
            print(
                f"Generated profile check failed: missing {args.output}",
                file=sys.stderr,
            )
            return 1
        actual = args.output.read_text(encoding="utf-8")
        if actual != expected:
            print(
                f"Generated profile check failed: {args.output} is not synchronized with "
                f"{args.data} in {args.mode} mode.",
                file=sys.stderr,
            )
            return 1
        _print_success(f"Generated profile is current: {args.output}")
        return 0
    output = write_profile(args.data, args.output, args.mode)
    line_count = len(output.read_text(encoding="utf-8").splitlines())
    _print_success(f"Generated {output} with {line_count} lines")
    return 0


def _print_success(message: str) -> None:
    """Print a Unicode success marker with an encoding-safe fallback."""
    decorated = f"{message} ✅"
    fallback = f"{message} [OK]"
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        decorated.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        decorated = fallback.encode(encoding, errors="backslashreplace").decode(
            encoding
        )
    print(decorated)


if __name__ == "__main__":
    raise SystemExit(main())
