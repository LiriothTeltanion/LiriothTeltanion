"""
Module: GitHub profile validator
Purpose: Catch broken local assets, duplicates, placeholders, and excessive README growth.
Author: Kevin "Lirioth" Cusnir
Date: 2026-07-15 | TZ: Asia/Jerusalem
Notes: Minimal deps; comments in ENGLISH; emojis sparingly.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_README = ROOT / "README.md"
DEFAULT_PROFILE_DATA = ROOT / "profile.json"
DEFAULT_LOCALIZED_PROFILES = {
    "es": ROOT / "PROFILE_ES.md",
    "he": ROOT / "PROFILE_HE.md",
}
LOCAL_LINK = re.compile(r"(?:src=|\]\()\"?(\./[^\"\) >]+)")
HTTP_URL = re.compile(r"https?://[^\s<>\"')\]]+")


def build_parser() -> argparse.ArgumentParser:
    """Create the profile-validation CLI parser.

    Returns:
        Configured parser.

    Raises:
        None.

    Example:
        >>> build_parser().prog
        'validate_profile'
    """
    parser = argparse.ArgumentParser(
        prog="validate_profile",
        description="Validate recruiter-facing GitHub profile structure.",
    )
    parser.add_argument("--readme", type=Path, default=DEFAULT_README)
    parser.add_argument("--max-lines", type=int, default=300)
    parser.add_argument(
        "--mode",
        choices=("compact", "expanded"),
        default="compact",
        help="Apply the structure contract for the selected generated profile mode.",
    )
    parser.add_argument(
        "--check-localized",
        action="store_true",
        help="Also verify that Spanish and Hebrew profiles retain canonical links and identity.",
    )
    parser.add_argument(
        "--profile-data",
        type=Path,
        default=DEFAULT_PROFILE_DATA,
        help="Canonical JSON used by the optional localized-profile check.",
    )
    return parser


def validate_profile(
    readme: Path,
    max_lines: int = 300,
    mode: str = "compact",
) -> list[str]:
    """Return all profile-quality problems instead of failing at the first one.

    Args:
        readme: Markdown profile file.
        max_lines: Maximum recruiter-facing line count.
        mode: Generated profile structure to enforce.

    Returns:
        List of actionable validation messages.

    Raises:
        FileNotFoundError: If the README does not exist.

    Example:
        >>> validate_profile(DEFAULT_README, 400, "compact")
        []
    """
    if not readme.exists():
        raise FileNotFoundError(f"README not found: {readme}")
    if mode not in {"compact", "expanded"}:
        raise ValueError("Mode must be compact or expanded.")
    content = readme.read_text(encoding="utf-8")
    lines = content.splitlines()
    problems: list[str] = []

    if len(lines) > max_lines:
        problems.append(f"README has {len(lines)} lines; target is at most {max_lines}.")
    if content.count("# Kevin Cusnir") != 1:
        problems.append("README must contain exactly one main Kevin Cusnir heading.")
    if ".example" in content:
        problems.append("Placeholder .example domain detected.")
    if "TODO" in content or "TBD" in content:
        problems.append("Unresolved TODO/TBD marker detected.")
    if content.count("## 🤝 Contact") != 1:
        problems.append("README must contain exactly one Contact section.")
    compact_summary = "Engineering approach and transferable strengths"
    expanded_headings = (
        "## 🧠 Engineering approach and strengths",
        "## 🎓 Education and structured learning",
        "## 🧙‍♂️ Kevin and Lirioth",
    )
    if mode == "compact":
        if compact_summary not in content:
            problems.append("Compact profile must keep secondary sections collapsible.")
        for heading in expanded_headings:
            if heading in content:
                problems.append(
                    f"Compact profile unexpectedly contains expanded heading: {heading}"
                )
    else:
        if compact_summary in content:
            problems.append("Expanded profile must not use the compact secondary-section summary.")
        for heading in expanded_headings:
            if heading not in content:
                problems.append(f"Expanded profile is missing heading: {heading}")

    for match in LOCAL_LINK.finditer(content):
        relative = match.group(1).split("#", 1)[0]
        path = (readme.parent / relative).resolve()
        if not path.exists():
            problems.append(f"Missing local asset or document: {relative}")

    required_assets = (
        "assets/profile-banner-animated.svg",
        "assets/profile-banner-static.svg",
        "assets/world-globe-animated.svg",
        "assets/world-globe-mobile.svg",
        "assets/world-globe-mobile-static.svg",
        "assets/world-globe-static.svg",
    )
    for relative in required_assets:
        if not (readme.parent / relative).exists():
            problems.append(f"Required asset missing: {relative}")

    return problems


def validate_localized_profiles(
    profile_data: Path = DEFAULT_PROFILE_DATA,
    localized_profiles: Mapping[str, Path] = DEFAULT_LOCALIZED_PROFILES,
) -> list[str]:
    """Check stable identity and link parity across Spanish and Hebrew profiles.

    Translated prose remains intentionally human-owned. This contract checks only
    facts that can be compared safely without pretending to translate text.
    """
    if not profile_data.exists():
        raise FileNotFoundError(f"Profile data not found: {profile_data}")
    data: Any = json.loads(profile_data.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Profile JSON root must be an object.")

    identity = _mapping(data.get("identity"), "profile.identity")
    links = _mapping(data.get("links"), "profile.links")
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        raise ValueError("profile.projects must be a non-empty array.")

    stable_urls = {
        _text(links.get("github"), "profile.links.github"),
        _text(links.get("linkedin"), "profile.links.linkedin"),
        _text(links.get("email"), "profile.links.email"),
    }
    for index, raw_project in enumerate(projects):
        project = _mapping(raw_project, f"profile.projects[{index}]")
        stable_urls.add(_text(project.get("source"), f"profile.projects[{index}].source"))
        demo = project.get("demo")
        if demo is not None:
            stable_urls.add(_text(demo, f"profile.projects[{index}].demo"))

    locale_cv_fields = {"es": "cv_es", "he": "cv_he"}
    problems: list[str] = []
    for locale, path in localized_profiles.items():
        if not path.exists():
            problems.append(f"Missing localized profile: {path.name}")
            continue
        content = path.read_text(encoding="utf-8")
        heading = (
            f"# {_text(identity.get('name'), 'profile.identity.name')} · "
            f"{_text(identity.get('alias'), 'profile.identity.alias')}"
        )
        if content.count(heading) != 1:
            problems.append(f"{path.name} must contain exactly one canonical identity heading.")

        present_urls = set(HTTP_URL.findall(content))
        mailto = _text(links.get("email"), "profile.links.email")
        if mailto in content:
            present_urls.add(mailto)
        for missing_url in sorted(stable_urls - present_urls):
            problems.append(f"{path.name} is missing canonical URL: {missing_url}")

        cv_field = locale_cv_fields.get(locale)
        if cv_field:
            cv_url = _text(links.get(cv_field), f"profile.links.{cv_field}")
            if cv_url not in present_urls:
                problems.append(f"{path.name} is missing its localized CV URL: {cv_url}")

        for navigation_target in ("./README.md", "./PROFILE_ES.md", "./PROFILE_HE.md"):
            if navigation_target == f"./{path.name}":
                continue
            if navigation_target not in content:
                problems.append(f"{path.name} is missing language navigation: {navigation_target}")

    return problems


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    """Return a JSON object for localized-profile consistency checks."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object.")
    return value


def _text(value: Any, path: str) -> str:
    """Return required canonical text for localized-profile checks."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path} must be a non-empty string.")
    return value


def main() -> int:
    """Validate the generated profile and print a concise result.

    Returns:
        ``0`` when valid, otherwise ``1``.

    Raises:
        FileNotFoundError: If the selected README is absent.

    Example:
        >>> main()  # doctest: +SKIP
        0
    """
    args = build_parser().parse_args()
    problems = validate_profile(args.readme, args.max_lines, args.mode)
    if args.check_localized:
        problems.extend(validate_localized_profiles(args.profile_data))
    if problems:
        print("Profile validation failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    line_count = len(args.readme.read_text(encoding="utf-8").splitlines())
    _print_success(f"Profile validation passed: {line_count} lines")
    return 0


def _print_success(message: str) -> None:
    """Print a Unicode success marker with an encoding-safe fallback."""
    decorated = f"{message} ✅"
    fallback = f"{message} [OK]"
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        decorated.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        decorated = fallback.encode(encoding, errors="backslashreplace").decode(encoding)
    print(decorated)


if __name__ == "__main__":
    raise SystemExit(main())
