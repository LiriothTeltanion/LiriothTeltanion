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
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "profile.json"
DEFAULT_OUTPUT = ROOT / "README.md"


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
    """Load and minimally validate profile JSON.

    Args:
        path: JSON source path.

    Returns:
        Parsed profile mapping.

    Raises:
        FileNotFoundError: If the source does not exist.
        json.JSONDecodeError: If the source is not valid JSON.
        ValueError: If required sections are absent.

    Example:
        >>> 'identity' in load_profile(DEFAULT_DATA)
        True
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Profile JSON root must be an object.")
    required = {"identity", "links", "projects", "skills", "languages"}
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"Missing profile sections: {', '.join(missing)}")
    return data


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
        '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/profile-banner-static.svg" />',
        '  <img src="./assets/profile-banner-animated.svg" width="100%" alt="Kevin Cusnir — frontend and full-stack developer profile banner" />',
        "</picture>",
        "",
        f"# {identity['name']} · {identity['alias']} ✨",
        "",
        f"### {identity['headline']}",
        "",
        f"**{identity['positioning']}**",
        "",
        _badge("LinkedIn", "Kevin Cusnir", "0A66C2", "linkedin", links["linkedin"]),
        _badge("CV", "English", "2563EB", "readme", links["cv_en"]),
        _badge("Email", "Contact", "EA4335", "gmail", links["email"]),
        _badge("Live", "Nova Music Lab", "7C3AED", "githubpages", projects[0]["demo"]),
        "",
        _small_badge("Open to", "Junior Frontend & Full-Stack Roles", "2EA44F"),
        _small_badge("Based in", identity["location"], "1F6FEB"),
        _small_badge("Languages", "Spanish · English · Hebrew", "F59E0B"),
        "",
        "[Snapshot](#-recruiter-snapshot) · [Projects](#-featured-projects) · [Evidence](#-engineering-evidence) · [Global](#-global-communication) · [Contact](#-contact)",
        "",
        "</div>",
        "",
        "---",
        "",
        "## ⚡ Recruiter snapshot",
        "",
        f"**{identity['name']}** is a junior frontend and full-stack developer in **{identity['location']}**. {identity['positioning']}",
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
        '<img src="./assets/portfolio-command-center-animated.svg" width="100%" alt="Animated command center for four featured portfolio projects" />',
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
        '<img src="./assets/project-constellation-animated.svg" width="100%" alt="Animated constellation of Kevin Cusnir featured projects" />',
        "",
    ]

    for project in projects:
        lines.extend(_render_project(project))

    lines.extend(
        [
            "<details>",
            '<summary><strong>💙 Open the NovaFit Ultimate 4.0 product tour</strong></summary>',
            "",
            '<img src="./assets/novafit-ultimate-tour.gif" width="100%" alt="Animated tour of NovaFit Ultimate analytics, recommendations, profiles and motivation" />',
            "",
            "**Why this project matters:** it turns a formerly broken public repository into a complete Python product with multi-user data isolation, a real Tkinter interface, trilingual UX, an automation-friendly CLI, safe migrations, explainable recommendations, ambitious analytics, portable reports and Windows launchers.",
            "",
            '<img src="./assets/novafit-ultimate-gui.png" width="100%" alt="Real NovaFit Ultimate 4.0 Tkinter Wellness Command Center" />',
            "",
            '<img src="./assets/analytics-training-atlas.png" width="100%" alt="NovaFit Training Atlas analytical workspace" />',
            "",
            "[Explore the NovaFit source](https://github.com/LiriothTeltanion/NovaFit)",
            "",
            "</details>",
            "",
            "<details>",
            '<summary><strong>🌍 Open profiles, EN/ES/HE, RTL and Sport & Data Coach</strong></summary>',
            "",
            '<img src="./assets/multi-profile-i18n-animated.svg" width="100%" alt="Animated NovaFit multi-profile and trilingual architecture" />',
            "",
            '<img src="./assets/multi-profile-language-center.png" width="100%" alt="Real NovaFit local profile manager" />',
            "",
            '<img src="./assets/sport-data-engine-animated.svg" width="100%" alt="Animated explainable Sport and Data Coach pipeline" />',
            "",
            '<img src="./assets/sport-data-coach-real.png" width="100%" alt="Real NovaFit Sport and Data Coach" />',
            "",
            "Each profile owns isolated records, goals, language, theme and activity preferences. English and Spanish use LTR; Hebrew moves the shell to RTL. Suggestions expose data confidence and reasons while avoiding medical claims.",
            "",
            "</details>",
            "",
            "<details>",
            '<summary><strong>🎨 Open Motivation Center and twelve-theme system</strong></summary>',
            "",
            '<img src="./assets/motivation-center-ultimate.png" width="100%" alt="Real NovaFit Ultimate Motivation Center" />',
            "",
            '<img src="./assets/theme-spectrum.png" width="100%" alt="Twelve-theme NovaFit analytics contact sheet" />',
            "",
            "**Twelve themes:** Midnight Neon · Aurora Borealis · Negev Sunrise · Ocean Depth · Forest Focus · Rose Quartz · Cloud Day · Solar Paper · High Contrast · Royal Sapphire · Cyber Lime · Sunset Arcade.",
            "",
            "</details>",
            "",
            "<details>",
            '<summary><strong>🪟 Open self-healing verification and distribution safety</strong></summary>',
            "",
            '<img src="./assets/self-healing-verification-animated.svg" width="100%" alt="Animated self-healing Windows setup and verification pipeline" />',
            "",
            '<img src="./assets/distribution-safety-animated.svg" width="100%" alt="Animated workspace-safe audit and clean release staging" />',
            "",
            "The checker repairs a local `.venv`, validates Matplotlib and `Asia/Jerusalem`, runs 74 tests, preserves an existing user database in workspace mode, and uses strict clean staging for downloadable releases.",
            "",
            "</details>",
            "",
            "---",
            "",
            "## 🧪 Engineering evidence",
            "",
            '<img src="./assets/engineering-orbit-animated.svg" width="100%" alt="Animated engineering orbit connecting frontend, Python, data, accessibility and delivery" />',
            "",
            "> These are project evidence counts, not invented proficiency percentages.",
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
            '  <source media="(prefers-reduced-motion: reduce)" srcset="./assets/world-globe-static.svg" />',
            '  <img src="./assets/world-globe-animated.svg" width="100%" alt="Animated globe showing Beersheba roots and Spanish, English and Hebrew collaboration" />',
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
            '<img src="./assets/learning-roadmap-animated.svg" width="100%" alt="Animated roadmap from frontend evidence to production full-stack delivery" />',
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
        >>> write_profile(DEFAULT_DATA, ROOT / 'README.preview.md', 'compact').suffix
        '.md'
    """
    content = render_profile(load_profile(data_path), mode)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(output_path)
    return output_path


def _render_project(project: Mapping[str, Any]) -> list[str]:
    links = [f"[Source]({project['source']})"]
    if project.get("demo"):
        links.insert(0, f"[Live demo]({project['demo']})")
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
        "The goal is not to decorate weak engineering. It is to make technically sound products easier to understand, remember and enjoy.",
    ]
    return {"approach": approach, "education": education_lines, "identity": identity_lines}


def _join(values: Sequence[str]) -> str:
    return " · ".join(values)


def _badge(label: str, value: str, color: str, logo: str, url: str | None) -> str:
    if not url:
        return ""
    safe_label = quote(label.replace("-", "--"), safe="")
    safe_value = quote(value.replace("-", "--"), safe="")
    return (
        f'<a href="{url}"><img src="https://img.shields.io/badge/'
        f'{safe_label}-{safe_value}-{color}?style=for-the-badge&logo={logo}&logoColor=white" '
        f'alt="{label}: {value}" /></a>'
    )


def _small_badge(label: str, value: str, color: str) -> str:
    safe_label = quote(label.replace("-", "--"), safe="")
    safe_value = quote(value.replace("-", "--"), safe="")
    return (
        f'<img src="https://img.shields.io/badge/{safe_label}-{safe_value}-{color}?style=flat-square" '
        f'alt="{label}: {value}" />'
    )


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
    print(f"Generated {output} with {line_count} lines ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
