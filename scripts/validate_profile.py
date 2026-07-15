"""
Module: GitHub profile validator
Purpose: Catch broken local assets, duplicates, placeholders, and excessive README growth.
Author: Kevin "Lirioth" Cusnir
Date: 2026-07-15 | TZ: Asia/Jerusalem
Notes: Minimal deps; comments in ENGLISH; emojis sparingly.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_README = ROOT / "README.md"
LOCAL_LINK = re.compile(r"(?:src=|\]\()\"?(\./[^\"\) >]+)")


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
    return parser


def validate_profile(readme: Path, max_lines: int = 300) -> list[str]:
    """Return all profile-quality problems instead of failing at the first one.

    Args:
        readme: Markdown profile file.
        max_lines: Maximum recruiter-facing line count.

    Returns:
        List of actionable validation messages.

    Raises:
        FileNotFoundError: If the README does not exist.

    Example:
        >>> validate_profile(DEFAULT_README, 400)
        []
    """
    if not readme.exists():
        raise FileNotFoundError(f"README not found: {readme}")
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
    if "<details>" not in content:
        problems.append("Compact profile should use collapsible secondary sections.")

    for match in LOCAL_LINK.finditer(content):
        relative = match.group(1).split("#", 1)[0]
        path = (readme.parent / relative).resolve()
        if not path.exists():
            problems.append(f"Missing local asset or document: {relative}")

    required_assets = (
        "assets/profile-banner-animated.svg",
        "assets/profile-banner-static.svg",
        "assets/world-globe-animated.svg",
        "assets/world-globe-static.svg",
    )
    for relative in required_assets:
        if not (readme.parent / relative).exists():
            problems.append(f"Required asset missing: {relative}")

    return problems


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
    problems = validate_profile(args.readme, args.max_lines)
    if problems:
        print("Profile validation failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    line_count = len(args.readme.read_text(encoding="utf-8").splitlines())
    print(f"Profile validation passed: {line_count} lines ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
