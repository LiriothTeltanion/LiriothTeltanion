"""Focused regression tests for the profile builder and validator CLIs."""

from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

from scripts import build_profile, validate_profile


ROOT = Path(__file__).resolve().parent.parent


class ProfileDataValidationTests(unittest.TestCase):
    """Exercise malformed profile data before it reaches the renderer."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.valid_data = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))

    def load(self, data: dict[str, Any]) -> dict[str, Any]:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "profile.json"
            source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return build_profile.load_profile(source)

    def test_missing_required_top_level_section_is_actionable(self) -> None:
        data = copy.deepcopy(self.valid_data)
        del data["growth"]

        with self.assertRaisesRegex(ValueError, r"Missing profile sections: growth"):
            self.load(data)

    def test_missing_nested_field_is_actionable(self) -> None:
        data = copy.deepcopy(self.valid_data)
        del data["identity"]["alias"]

        with self.assertRaisesRegex(ValueError, r"profile\.identity: alias"):
            self.load(data)

    def test_empty_projects_fail_before_rendering(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["projects"] = []

        with self.assertRaisesRegex(ValueError, r"profile\.projects must contain at least one item"):
            self.load(data)

    def test_flagship_project_must_be_first(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["projects"][0], data["projects"][1] = data["projects"][1], data["projects"][0]

        with self.assertRaisesRegex(ValueError, r"Nova Music Lab.*first"):
            self.load(data)


class Cp1252OutputTests(unittest.TestCase):
    """Keep both Windows CLI success paths safe outside UTF-8 terminals."""

    def capture_cp1252(self, callback: Callable[[], int]) -> tuple[int, str]:
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="cp1252")
        try:
            with patch.object(sys, "stdout", stream):
                result = callback()
                stream.flush()
            output = buffer.getvalue().decode("cp1252")
            return result, output
        finally:
            stream.detach()

    def test_builder_success_output_falls_back_to_ascii(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "README.md"
            arguments = [
                "build_profile",
                "--data",
                str(ROOT / "profile.json"),
                "--output",
                str(output),
            ]
            with patch.object(sys, "argv", arguments):
                result, console = self.capture_cp1252(build_profile.main)

        self.assertEqual(result, 0)
        self.assertIn("[OK]", console)

    def test_validator_success_output_falls_back_to_ascii(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "assets"
            assets.mkdir()
            for name in (
                "profile-banner-animated.svg",
                "profile-banner-static.svg",
                "world-globe-animated.svg",
                "world-globe-static.svg",
            ):
                (assets / name).write_text("<svg></svg>", encoding="utf-8")
            readme = root / "README.md"
            readme.write_text(
                "# Kevin Cusnir\n\n<details>\n</details>\n\n## 🤝 Contact\n",
                encoding="utf-8",
            )
            arguments = ["validate_profile", "--readme", str(readme)]
            with patch.object(sys, "argv", arguments):
                result, console = self.capture_cp1252(validate_profile.main)

        self.assertEqual(result, 0)
        self.assertIn("[OK]", console)


class GeneratedProfileContractTests(unittest.TestCase):
    """Protect the responsive visual contract and generated-file synchronization."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = build_profile.load_profile(ROOT / "profile.json")

    def test_compact_profile_keeps_responsive_and_privacy_contracts(self) -> None:
        content = build_profile.render_profile(self.data, "compact")

        self.assertLessEqual(len(content.splitlines()), 300)
        for expected in (
            "profile-banner-mobile-static.svg",
            "portfolio-command-center-mobile-static.svg",
            "nova-music-journey-static.svg",
            "nova-music-journey-mobile-static.svg",
            "motivation-center-mobile.svg",
            "novafit-trust-system-mobile.svg",
            "world-globe-mobile.svg",
            "learning-roadmap-mobile.svg",
            "seeded demonstration records",
            "Nova Music Lab source",
        ):
            self.assertIn(expected, content)
        for forbidden in (
            "novafit-ultimate-tour.gif",
            "novafit-analytics-tour.gif",
            "novafit-ultimate-gui.png",
            "motivation-center-ultimate.png",
            "multi-profile-language-center.png",
            "sport-data-coach-real.png",
            "img.shields.io",
        ):
            self.assertNotIn(forbidden, content)

    def test_generated_readmes_match_the_builder(self) -> None:
        compact = (ROOT / "README.md").read_text(encoding="utf-8")
        expanded = (ROOT / "README_EXPANDED.md").read_text(encoding="utf-8")

        self.assertEqual(compact, build_profile.render_profile(self.data, "compact"))
        self.assertEqual(expanded, build_profile.render_profile(self.data, "expanded"))
        self.assertNotIn(b"\r\n", (ROOT / "README.md").read_bytes())
        self.assertNotIn(b"\r\n", (ROOT / "README_EXPANDED.md").read_bytes())


if __name__ == "__main__":
    unittest.main()
