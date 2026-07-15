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
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    "projects",
    "skills",
    "strengths",
}
IDENTITY_FIELDS = (
    "alias",
    "availability",
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
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="Profile JSON source.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="README destination.")
    parser.add_argument(
        "--mode",
        choices=["compact", "expanded"],
        default="compact",
        help="Compact keeps secondary content inside details blocks.",
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
    identity = _require_mapping(data["identity"], "profile.identity", IDENTITY_FIELDS)
    for field in IDENTITY_FIELDS:
        _require_text(identity[field], f"profile.identity.{field}")

    links = _require_mapping(data["links"], "profile.links", LINK_FIELDS)
    for field in LINK_FIELDS:
        _require_text(links[field], f"profile.links.{field}")

    projects = _require_list(data["projects"], "profile.projects")
    for index, raw_project in enumerate(projects):
        path = f"profile.projects[{index}]"
        project = _require_mapping(raw_project, path, PROJECT_FIELDS)
        for field in PROJECT_FIELDS:
            if field == "demo" and project[field] is None:
                continue
            _require_text(project[field], f"{path}.{field}")
        if "role_signal" in project:
            _require_text(project["role_signal"], f"{path}.role_signal")
        if "highlights" in project:
            _require_text_list(project["highlights"], f"{path}.highlights", allow_empty=True)

    flagship = projects[0]
    if flagship["name"] != "Nova Music Lab":
        raise ValueError(
            "profile.projects must list 'Nova Music Lab' first because the header Live badge "
            "uses the first project's demo URL."
        )
    _require_text(flagship["demo"], "profile.projects[0].demo")

    skills = _require_mapping(data["skills"], "profile.skills", SKILL_FIELDS)
    for field in SKILL_FIELDS:
        _require_text_list(skills[field], f"profile.skills.{field}")

    languages = _require_list(data["languages"], "profile.languages")
    for index, raw_language in enumerate(languages):
        path = f"profile.languages[{index}]"
        language = _require_mapping(raw_language, path, LANGUAGE_FIELDS)
        for field in LANGUAGE_FIELDS:
            _require_text(language[field], f"{path}.{field}")

    evidence_counts = _require_list(data["evidence_counts"], "profile.evidence_counts")
    for index, raw_item in enumerate(evidence_counts):
        path = f"profile.evidence_counts[{index}]"
        item = _require_mapping(raw_item, path, EVIDENCE_FIELDS)
        _require_text(item["label"], f"{path}.label")
        if item["value"] is None or (isinstance(item["value"], str) and not item["value"].strip()):
            raise ValueError(f"{path}.value must not be empty.")

    _require_text_list(data["strengths"], "profile.strengths")
    _require_text_list(data["growth"], "profile.growth")

    education = _require_mapping(data["education"], "profile.education", EDUCATION_FIELDS)
    for field in EDUCATION_FIELDS:
        _require_text(education[field], f"profile.education.{field}")

    if "review_path" in data:
        review_path = _require_list(data["review_path"], "profile.review_path", allow_empty=True)
        for index, raw_item in enumerate(review_path):
            path = f"profile.review_path[{index}]"
            item = _require_mapping(raw_item, path, REVIEW_PATH_FIELDS)
            for field in REVIEW_PATH_FIELDS:
                _require_text(item[field], f"{path}.{field}")


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


def _require_text_list(value: Any, path: str, *, allow_empty: bool = False) -> list[Any]:
    """Validate an array containing only non-empty strings."""
    items = _require_list(value, path, allow_empty=allow_empty)
    for index, item in enumerate(items):
        _require_text(item, f"{path}[{index}]")
    return items


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
    projects = data["projects"]
    skills = data["skills"]

    lines: list[str] = [
        '<a id="top"></a>',
        "",
        '<div align="center">',
        "",
        '<picture>',
        '  <source media="(max-width: 640px) and (prefers-reduced-motion: reduce)" srcset="./assets/profile-banner-mobile-static.svg" />',
        '  <source media="(max-width: 640px)" srcset="./assets/profile-banner-mobile-animated.svg" />',
        '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/profile-banner-static.svg" />',
        '  <img src="./assets/profile-banner-animated.svg" width="100%" alt="Kevin Cusnir and Lirioth Teltanion — frontend, full-stack and creative engineering profile" />',
        "</picture>",
        "",
        f"# {identity['name']} · {identity['alias']} ✨",
        "",
        f"<p><strong>{identity['headline']}</strong></p>",
        "",
        f"**{identity['positioning']}**",
        "",
        f"[💼 LinkedIn]({links['linkedin']}) · [📄 CV EN]({links['cv_en']}) · [CV ES]({links['cv_es']}) · [CV HE]({links['cv_he']}) · [✉️ Email]({links['email']}) · [🎧 Nova Music Lab live]({projects[0]['demo']})",
        "",
        f"**Open to:** Junior Frontend & Full-Stack roles · **Based in:** {identity['location']} · **Languages:** ES · EN · HE",
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
        f"I’m **{identity['name']}**, a junior frontend and full-stack developer in **{identity['location']}**. {identity['positioning']}",
        "",
        f"> **Availability:** {identity['availability']}.",
        "",
        "| What I can prove publicly | Strongest evidence |",
        "|---|---|",
        "| React and TypeScript product work | Nova Music Lab and Christopher Rodríguez Portfolio |",
        "| Python, SQLite and desktop workflows | NovaFit Ultimate 4.0 and Fullstack2026 |",
        "| Data transformation and honesty | Multi-source music import, deduplication, validation and coverage labels |",
        "| Accessibility and multilingual UX | EN/ES/HE, RTL behavior, keyboard use and reduced-motion support |",
        "| Delivery discipline | Automated tests, CI, GitHub Pages, bundle budgets and release checklists |",
        "",
        "**Best fit:** a junior role with real users, respectful code review, mentorship, product quality and room for structured creativity.",
        "",
        '<picture>',
        '  <source media="(max-width: 640px) and (prefers-reduced-motion: reduce)" srcset="./assets/portfolio-command-center-mobile-static.svg" />',
        '  <source media="(max-width: 640px)" srcset="./assets/portfolio-command-center-mobile.svg" />',
        '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/portfolio-command-center-static.svg" />',
        '  <img src="./assets/portfolio-command-center-animated.svg" width="100%" alt="Four featured projects with their scope, stack, accessibility and delivery evidence" />',
        '</picture>',
        "",
        "### A reviewer-friendly path",
        "",
        "| Time | What to inspect | What it proves |",
        "|---:|---|---|",
        *[
            f"| **{item['time']}** | {item['action']} | {item['evidence']} |"
            for item in data.get("review_path", [])
        ],
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
        elif project["name"] == "NovaFit":
            lines.extend(_render_novafit_spotlights(project))

    lines.extend(
        [
            "---",
            "",
            "## 🧪 Engineering evidence",
            "",
            '<img src="./assets/engineering-orbit-animated.svg" width="100%" alt="Product engineering connects frontend, Python, data, accessibility, privacy, testing and delivery" />',
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
            f"**Languages:** {_join(skills['languages'])}  ",
            f"**Frontend:** {_join(skills['frontend'])}  ",
            f"**Backend & data:** {_join(skills['backend_data'])}  ",
            f"**Testing & quality:** {_join(skills['quality'])}  ",
            f"**Workflow:** {_join(skills['workflow'])}",
            "",
            "---",
            "",
            "## 🌍 Global communication",
            "",
            '<picture>',
            '  <source media="(max-width: 640px)" srcset="./assets/world-globe-mobile.svg" />',
            '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/world-globe-static.svg" />',
            '  <img src="./assets/world-globe-animated.svg" width="100%" alt="Beersheba connects to Spanish, English and Hebrew product communication and localization" />',
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
            '<picture>',
            '  <source media="(max-width: 640px)" srcset="./assets/learning-roadmap-mobile.svg" />',
            '  <img src="./assets/learning-roadmap-animated.svg" width="100%" alt="Roadmap from proven frontend work through data and application trust to production full-stack delivery" />',
            "</picture>",
            "",
        ]
    )
    for item in data["growth"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "The next portfolio milestone is a deployed full-stack product with PostgreSQL, authentication, Docker, integration tests, structured logging and a documented demo account.",
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
        f"**Status:** {project['status']}  ",
        f"**Problem:** {project['problem']}  ",
        f"**Solution:** {project['solution']}  ",
        f"**Stack:** {project['stack']}  ",
        f"**Evidence:** {project['evidence']}  ",
        f"**Role signal:** {project.get('role_signal', 'Product engineering')}  ",
        f"**Highlights:** {' · '.join(project.get('highlights', []))}  " if project.get("highlights") else "",
        " · ".join(links),
        "",
    ]


def _render_nova_music_spotlight(project: Mapping[str, Any]) -> list[str]:
    """Render the flagship product journey directly after Nova Music Lab."""
    return [
        "<details>",
        '<summary><strong>🎧 Open the Nova Music Lab data journey</strong></summary>',
        "",
        '<picture>',
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


def _render_novafit_spotlights(project: Mapping[str, Any]) -> list[str]:
    """Render two focused NovaFit tours while keeping the main project list scannable."""
    return [
        "<details>",
        '<summary><strong>💙 Open the NovaFit product, analytics and visual system</strong></summary>',
        "",
        "> **Public-data boundary:** the visuals below use profile-independent or seeded demonstration data; no personal wellness history is displayed.",
        "",
        '<picture>',
        '  <source media="(max-width: 640px)" srcset="./assets/motivation-center-mobile.svg" />',
        '  <img src="./assets/motivation-center-animated.svg" width="100%" alt="NovaFit Motivation Center connects purpose, small actions, evidence, celebration and recovery" />',
        "</picture>",
        "",
        "**Why this project matters:** NovaFit brings multi-user data isolation, a complete Tkinter interface, trilingual UX, automation-friendly CLI workflows, safe migrations, explainable suggestions, analytics, portable reports and Windows delivery into one local-first product.",
        "",
        '<a href="./assets/analytics-training-atlas.png"><img src="./assets/analytics-training-atlas.png" width="100%" alt="NovaFit Training Atlas workspace showing seeded analytical charts" /></a>',
        "",
        '<a href="./assets/theme-spectrum.png"><img src="./assets/theme-spectrum.png" width="100%" alt="NovaFit twelve-theme interface contact sheet" /></a>',
        "",
        "The Training Atlas is profile-independent; the theme contact sheet uses seeded demonstration records without publishing a profile name.",
        "",
        "**Twelve themes:** Midnight Neon · Aurora Borealis · Negev Sunrise · Ocean Depth · Forest Focus · Rose Quartz · Cloud Day · Solar Paper · High Contrast · Royal Sapphire · Cyber Lime · Sunset Arcade.",
        "",
        f"[Inspect the NovaFit source]({project['source']})",
        "",
        "</details>",
        "",
        "<details>",
        '<summary><strong>🌍 Open NovaFit profiles, EN/ES/HE, coach and safe delivery</strong></summary>',
        "",
        "> **Public-data boundary:** this system map contains no profile names, dates or wellness metrics.",
        "",
        '<picture>',
        '  <source media="(max-width: 640px)" srcset="./assets/novafit-trust-system-mobile.svg" />',
        '  <img src="./assets/novafit-trust-system-animated.svg" width="100%" alt="NovaFit protects profile boundaries, checks data quality, explains conservative suggestions, verifies the workspace and stages clean releases" />',
        "</picture>",
        "",
        "Each profile owns isolated records, goals, language, theme and activity preferences. English and Spanish use LTR; Hebrew moves the shell to RTL. Suggestions expose data confidence and reasons while avoiding medical claims.",
        "",
        "The checker repairs a local `.venv`, validates Matplotlib and `Asia/Jerusalem`, runs 74 tests, preserves an existing user database in workspace mode, and uses strict clean staging for downloadable releases.",
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
    return {"approach": approach, "education": education_lines, "identity": identity_lines}


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
        decorated = fallback.encode(encoding, errors="backslashreplace").decode(encoding)
    print(decorated)


if __name__ == "__main__":
    raise SystemExit(main())
