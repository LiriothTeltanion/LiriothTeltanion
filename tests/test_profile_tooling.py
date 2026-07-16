"""Focused regression tests for the profile builder and validator CLIs."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import math
import re
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

from scripts import build_profile, check_external_links, validate_profile
from tools.profile import generate_signature_assets, generate_world_globe


ROOT = Path(__file__).resolve().parent.parent


def point_to_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    """Return the shortest Euclidean distance from a point to a segment."""

    point_x, point_y = point
    start_x, start_y = start
    delta_x = end[0] - start_x
    delta_y = end[1] - start_y
    length_squared = delta_x**2 + delta_y**2
    if length_squared == 0:
        return math.hypot(point_x - start_x, point_y - start_y)
    projection = (
        (point_x - start_x) * delta_x + (point_y - start_y) * delta_y
    ) / length_squared
    projection = max(0.0, min(1.0, projection))
    closest_x = start_x + projection * delta_x
    closest_y = start_y + projection * delta_y
    return math.hypot(point_x - closest_x, point_y - closest_y)


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

    def test_missing_birthplace_is_actionable(self) -> None:
        data = copy.deepcopy(self.valid_data)
        del data["identity"]["birthplace"]

        with self.assertRaisesRegex(ValueError, r"profile\.identity: birthplace"):
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

    def test_public_links_must_use_https(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["links"]["github"] = "http://github.com/LiriothTeltanion"

        with self.assertRaisesRegex(ValueError, r"profile\.links\.github.*HTTPS"):
            self.load(data)

    def test_contact_email_must_be_a_simple_mailto_url(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["links"]["email"] = "mailto:kevincusnir@gmail.com?subject=Hello"

        with self.assertRaisesRegex(ValueError, r"profile\.links\.email.*simple mailto"):
            self.load(data)

    def test_duplicate_projects_are_rejected_case_insensitively(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["projects"][1]["name"] = "nova music lab"

        with self.assertRaisesRegex(ValueError, r"profile\.projects names.*duplicate"):
            self.load(data)

    def test_duplicate_skills_across_categories_are_rejected(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["skills"]["quality"].append(data["skills"]["languages"][0].lower())

        with self.assertRaisesRegex(ValueError, r"profile\.skills across categories.*duplicate"):
            self.load(data)

    def test_evidence_counts_require_non_negative_integers(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["evidence_counts"][0]["value"] = True

        with self.assertRaisesRegex(ValueError, r"non-negative integer"):
            self.load(data)

    def test_profile_version_requires_strict_semver(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["profile_version"] = "2.0"

        with self.assertRaisesRegex(ValueError, r"profile_version.*Semantic Versioning"):
            self.load(data)

    def test_release_tag_must_agree_with_profile_version(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["release"]["tag"] = "v2.0.0"

        with self.assertRaisesRegex(ValueError, r"release\.tag.*v2\.1\.0"):
            self.load(data)

    def test_release_prepared_date_must_be_iso_calendar_date(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["release"]["prepared_on"] = "2026-02-31"

        with self.assertRaisesRegex(ValueError, r"prepared_on.*YYYY-MM-DD"):
            self.load(data)

        data["release"]["prepared_on"] = "20260716"
        with self.assertRaisesRegex(ValueError, r"prepared_on.*YYYY-MM-DD"):
            self.load(data)

    def test_novafit_status_must_agree_with_manifest_version(self) -> None:
        data = copy.deepcopy(self.valid_data)
        novafit = next(project for project in data["projects"] if project["name"] == "NovaFit")
        novafit["status"] = "Active v4.1.0 local-first desktop product"

        with self.assertRaisesRegex(ValueError, r"NovaFit.*status.*portfolio_sync"):
            self.load(data)

    def test_novafit_tour_requires_one_canonical_static_fallback(self) -> None:
        data = copy.deepcopy(self.valid_data)
        novafit = next(project for project in data["projects"] if project["name"] == "NovaFit")
        novafit["media"]["mobile_static"] = "assets/novafit-product-tour-mobile.png"

        with self.assertRaisesRegex(ValueError, r"mobile_static.*canonical static"):
            self.load(data)

    def test_novafit_tour_rejects_remote_or_ambiguous_asset_paths(self) -> None:
        data = copy.deepcopy(self.valid_data)
        novafit = next(project for project in data["projects"] if project["name"] == "NovaFit")
        novafit["media"]["animation"] = "assets/novafit-product-tour.gif?raw=1"

        with self.assertRaisesRegex(ValueError, r"animation.*repository-relative"):
            self.load(data)

    def test_ivrit_must_be_second_and_test_totals_must_reconcile(self) -> None:
        data = copy.deepcopy(self.valid_data)
        data["projects"][1], data["projects"][2] = (
            data["projects"][2],
            data["projects"][1],
        )
        with self.assertRaisesRegex(ValueError, r"Ivrit Sheli.*second"):
            self.load(data)

        data = copy.deepcopy(self.valid_data)
        ivrit = next(project for project in data["projects"] if project["name"] == "Ivrit Sheli")
        ivrit["release_evidence"]["total_tests"] = 125
        with self.assertRaisesRegex(ValueError, r"total_tests.*backend_tests.*frontend_tests"):
            self.load(data)

    def test_ivrit_pending_live_status_and_media_are_strict(self) -> None:
        data = copy.deepcopy(self.valid_data)
        ivrit = next(project for project in data["projects"] if project["name"] == "Ivrit Sheli")
        ivrit["status"] = "Live v2.0.0 dual-mode full-stack product"
        with self.assertRaisesRegex(ValueError, r"Ivrit Sheli.*status.*verified live demo"):
            self.load(data)

        data = copy.deepcopy(self.valid_data)
        ivrit = next(project for project in data["projects"] if project["name"] == "Ivrit Sheli")
        ivrit["media"]["rtl_static"] = ivrit["media"]["static"]
        with self.assertRaisesRegex(ValueError, r"distinct animation, desktop, mobile and RTL"):
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
                "world-globe-mobile.svg",
                "world-globe-mobile-static.svg",
                "world-globe-static.svg",
            ):
                (assets / name).write_text("<svg></svg>", encoding="utf-8")
            readme = root / "README.md"
            readme.write_text(
                "# Kevin Cusnir\n\n<details>\n"
                "<summary>Engineering approach and transferable strengths</summary>\n"
                "</details>\n\n## 🤝 Contact\n",
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
            "profile-version: 2.1.0",
            "profile-banner-mobile-static.svg",
            "nova-music-live-preview-mobile.jpg",
            "nova-music-journey-static.svg",
            "nova-music-journey-mobile-static.svg",
            "ivrit-sheli-product-tour.gif",
            "ivrit-sheli-2-mobile.png",
            "ivrit-sheli-2-hebrew-rtl.png",
            "novafit-product-tour.gif",
            "novafit-product-tour-static.png",
            "novafit-trust-system-mobile.svg",
            "engineering-orbit-mobile-static.svg",
            "engineering-orbit-mobile.svg",
            "world-globe-mobile.svg",
            "world-globe-mobile-static.svg",
            "learning-roadmap-mobile.svg",
            "kc-lt-signature.svg",
            "kc-lt-signature-animated.svg",
            "seeded demonstration records",
            "clearly labeled seeded demo profiles",
            "deterministic synthetic records",
            "Verified v4.2.0 evidence",
            "124 discovered automated tests",
            "58 public visual assets",
            "Download the verified v4.2.0 release",
            "Nova Music Lab source",
            "109 backend + 17 frontend = 126 passing tests",
            "GitHub OAuth/PKCE",
            "PostgreSQL tenant RLS",
            "Live deployment pending",
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
            "The next portfolio milestone is a deployed full-stack product",
        ):
            self.assertNotIn(forbidden, content)
        self.assertIn("San Cristóbal, Venezuela", content)
        self.assertIn("Beersheba, Israel", content)
        self.assertIn("represent 195 sovereign states", content)

    def test_release_metadata_and_generated_modes_agree(self) -> None:
        version = self.data["profile_version"]
        release = self.data["release"]
        expected_marker = (
            f"<!-- profile-version: {version}; release-tag: {release['tag']}; "
            f"release-title: {release['title']} -->"
        )

        self.assertEqual(version, "2.1.0")
        self.assertEqual(release["tag"], f"v{version}")
        for mode in ("compact", "expanded"):
            self.assertTrue(
                build_profile.render_profile(self.data, mode).startswith(expected_marker)
            )

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## [{version}]", changelog)
        self.assertIn("Pre-versioned Ultimate profile baseline", changelog)

    def test_nova_music_lab_remains_the_strongest_first_flagship(self) -> None:
        content = build_profile.render_profile(self.data, "compact")

        self.assertEqual(self.data["projects"][0]["name"], "Nova Music Lab")
        self.assertLess(
            content.index("### 🎧 Nova Music Lab"), content.index("### א Ivrit Sheli")
        )
        self.assertLess(
            content.index("### א Ivrit Sheli"), content.index("### 💙 NovaFit")
        )
        self.assertLess(
            content.index("nova-music-live-preview.jpg"),
            content.index("ivrit-sheli-product-tour.gif"),
        )
        self.assertLess(
            content.index("ivrit-sheli-product-tour.gif"),
            content.index("novafit-product-tour.gif"),
        )

    def test_project_demo_urls_stay_with_the_correct_project(self) -> None:
        projects = {project["name"]: project for project in self.data["projects"]}

        self.assertIsNone(projects["Ivrit Sheli"]["demo"])
        self.assertEqual(
            projects["Ivrit Sheli"]["source"],
            "https://github.com/LiriothTeltanion/IvritSheli",
        )

        self.assertEqual(
            projects["NovaFit"]["demo"],
            "https://liriothteltanion.github.io/NovaFit/",
        )
        self.assertEqual(
            projects["Christopher Rodríguez Portfolio"]["demo"],
            "https://liriothteltanion.github.io/ChristopherRodriguezCVOnline/",
        )

    def test_globe_assets_represent_exact_sovereign_contract_and_route(self) -> None:
        filenames = (
            "world-globe-animated.svg",
            "world-globe-static.svg",
            "world-globe-mobile.svg",
            "world-globe-mobile-static.svg",
        )
        sovereign_codes = generate_world_globe.SOVEREIGN_ISO_A3
        expected_supplemental = set(
            generate_world_globe.SUPPLEMENTAL_SOVEREIGN_CENTROIDS
        )
        self.assertEqual(len(sovereign_codes), 195)
        self.assertEqual(len(expected_supplemental), 13)

        for filename in filenames:
            content = (ROOT / "assets" / filename).read_text(encoding="utf-8")
            for expected in (
                "San Cristóbal",
                "Venezuela",
                "Beersheba",
                "Israel",
                "Natural Earth",
                'data-iso="VEN"',
                'data-iso="ISR"',
                "195 SOVEREIGN STATES REPRESENTED / TINY STATES MARKED",
                "13 supplemental sovereign-centroid markers",
                "195 sovereign states represented (182 from pinned sources)",
            ):
                self.assertIn(expected, content, filename)

            country_codes = set(
                re.findall(r'data-layer="country"[^>]+data-iso="([^"]+)"', content)
            )
            tiny_codes = set(
                re.findall(
                    r'data-layer="tiny-country"[^>]+data-iso="([^"]+)"', content
                )
            )
            supplemental_codes = set(
                re.findall(
                    r'data-layer="supplemental-sovereign"[^>]+'
                    r'data-iso="([^"]+)"',
                    content,
                )
            )
            source_codes = country_codes | tiny_codes
            represented_sovereigns = (
                source_codes | supplemental_codes
            ) & sovereign_codes

            self.assertEqual(represented_sovereigns, sovereign_codes, filename)
            self.assertEqual(
                sovereign_codes - source_codes, expected_supplemental, filename
            )
            self.assertEqual(supplemental_codes, expected_supplemental, filename)
            self.assertTrue(source_codes.isdisjoint(supplemental_codes), filename)
            self.assertEqual(len(source_codes & sovereign_codes), 182, filename)
            self.assertEqual(content.count('data-layer="tiny-country"'), 37, filename)
            self.assertEqual(
                content.count('data-layer="supplemental-sovereign"'), 13, filename
            )
            self.assertEqual(
                content.count('data-source="deterministic-centroid"'), 13, filename
            )
            offset_codes = set(generate_world_globe.SUPPLEMENTAL_MARKER_OFFSETS)
            self.assertEqual(
                content.count('data-layer="supplemental-leader"'),
                len(offset_codes),
                filename,
            )
            for iso in offset_codes:
                self.assertIn(
                    f'data-layer="supplemental-leader" data-iso="{iso}"',
                    content,
                    filename,
                )

            positions = {
                iso: (float(x), float(y))
                for iso, x, y in re.findall(
                    r'<circle data-layer="supplemental-sovereign"[^>]+'
                    r'data-iso="([A-Z]{3})"[^>]+cx="([0-9.-]+)" '
                    r'cy="([0-9.-]+)"',
                    content,
                )
            }
            for left_index, left_iso in enumerate(sorted(offset_codes)):
                for right_iso in sorted(offset_codes)[left_index + 1 :]:
                    left_x, left_y = positions[left_iso]
                    right_x, right_y = positions[right_iso]
                    distance_squared = (left_x - right_x) ** 2 + (
                        left_y - right_y
                    ) ** 2
                    self.assertGreater(distance_squared, 36.0, filename)

            leader_segments = {
                iso: tuple(float(value) for value in coordinates)
                for iso, *coordinates in re.findall(
                    r'<path data-layer="supplemental-leader" '
                    r'data-iso="([A-Z]{3})"[^>]+d="M([0-9.-]+) ([0-9.-]+)'
                    r'L([0-9.-]+) ([0-9.-]+)"',
                    content,
                )
            }
            visible_markers = [
                (layer, iso, float(x), float(y), float(radius))
                for layer, iso, x, y, radius in re.findall(
                    r'<circle data-layer="(tiny-country|supplemental-sovereign)"'
                    r'[^>]+data-iso="([A-Z]{3})"[^>]+ cx="([0-9.-]+)" '
                    r'cy="([0-9.-]+)" r="([0-9.-]+)"',
                    content,
                )
            ]
            leader_half_width = 0.75 / 2
            for leader_iso, (start_x, start_y, end_x, end_y) in (
                leader_segments.items()
            ):
                for layer, marker_iso, x, y, radius in visible_markers:
                    if layer == "supplemental-sovereign" and marker_iso == leader_iso:
                        continue
                    clearance = point_to_segment_distance(
                        (x, y), (start_x, start_y), (end_x, end_y)
                    ) - radius - leader_half_width
                    self.assertGreater(
                        clearance,
                        0.0,
                        f"{filename}: {leader_iso} leader crosses {marker_iso}",
                    )
            self.assertIn("PSE", source_codes, filename)
            self.assertNotIn("PSX", source_codes, filename)

    def test_generated_readmes_match_the_builder(self) -> None:
        compact = (ROOT / "README.md").read_text(encoding="utf-8")
        expanded = (ROOT / "README_EXPANDED.md").read_text(encoding="utf-8")

        self.assertEqual(compact, build_profile.render_profile(self.data, "compact"))
        self.assertEqual(expanded, build_profile.render_profile(self.data, "expanded"))
        self.assertNotIn(b"\r\n", (ROOT / "README.md").read_bytes())
        self.assertNotIn(b"\r\n", (ROOT / "README_EXPANDED.md").read_bytes())

    def test_both_generated_modes_pass_the_light_validator(self) -> None:
        self.assertEqual(
            validate_profile.validate_profile(ROOT / "README.md", 300, "compact"),
            [],
        )
        self.assertEqual(
            validate_profile.validate_profile(
                ROOT / "README_EXPANDED.md", 300, "expanded"
            ),
            [],
        )

    def test_localized_profiles_keep_canonical_identity_and_links(self) -> None:
        self.assertEqual(validate_profile.validate_localized_profiles(), [])

    def test_builder_check_mode_detects_drift_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "README.md"
            output.write_text("stale\n", encoding="utf-8")
            arguments = [
                "build_profile",
                "--data",
                str(ROOT / "profile.json"),
                "--output",
                str(output),
                "--mode",
                "compact",
                "--check",
            ]
            with patch.object(sys, "argv", arguments), patch.object(sys, "stderr", io.StringIO()):
                result = build_profile.main()

            self.assertEqual(result, 1)
            self.assertEqual(output.read_text(encoding="utf-8"), "stale\n")


class SignatureAssetTests(unittest.TestCase):
    """Protect the eight-stroke KC star LT geometry and restrained motion."""

    namespace = "{http://www.w3.org/2000/svg}"

    def assert_signature_contract(
        self, path: Path, expected_star_transform: str
    ) -> None:
        root = ET.parse(path).getroot()
        ink_groups = root.findall(
            f'.//{self.namespace}g[@class="signature-ink"]'
        )
        stars = root.findall(f'.//{self.namespace}g[@class="signature-star"]')
        placements = root.findall(
            f'.//{self.namespace}g[@class="signature-star-placement"]'
        )
        self.assertEqual(len(ink_groups), 1, path.name)
        self.assertEqual(
            len(ink_groups[0].findall(f"./{self.namespace}path")), 8, path.name
        )
        self.assertEqual(len(stars), 1, path.name)
        self.assertEqual(len(placements), 1, path.name)
        self.assertEqual(
            placements[0].get("transform"), expected_star_transform, path.name
        )
        self.assertIsNone(stars[0].get("transform"), path.name)
        self.assertEqual(stars[0].get("aria-hidden"), "true", path.name)

    def test_brand_variants_keep_eight_pen_strokes_and_one_star(self) -> None:
        variants = {
            "kc-lt-signature.svg": "translate(346 110)",
            "kc-lt-signature-animated.svg": "translate(346 110)",
            "kc-lt-signature-light.svg": "translate(346 110)",
            "kc-lt-signature-monochrome.svg": "translate(346 110)",
            "kc-lt-signature-compact.svg": "translate(178 94)",
        }
        for filename, transform in variants.items():
            self.assert_signature_contract(
                ROOT / "assets" / "brand" / filename, transform
            )

        monochrome = ET.parse(
            ROOT / "assets" / "brand" / "kc-lt-signature-monochrome.svg"
        ).getroot()
        star = monochrome.find(
            f'.//{self.namespace}g[@class="signature-star"]'
        )
        self.assertIsNotNone(star)
        self.assertIsNone(star.get("filter"))

    def test_star_palette_glow_and_one_time_reveal_are_exact(self) -> None:
        self.assertEqual(
            generate_signature_assets.FULL_STAR,
            generate_signature_assets.StarSpec(346, 110, 18, 22, 2.6),
        )
        self.assertEqual(
            generate_signature_assets.COMPACT_STAR,
            generate_signature_assets.StarSpec(178, 94, 12, 16, 1.8),
        )
        master = ET.parse(
            ROOT / "assets" / "brand" / "kc-lt-signature.svg"
        ).getroot()
        star = master.find(f'.//{self.namespace}g[@class="signature-star"]')
        self.assertIsNotNone(star)
        self.assertEqual(star.get("filter"), "url(#starGlow)")
        fills = {
            shape.get("fill") for shape in star.findall(f"./{self.namespace}path")
        }
        self.assertEqual(
            fills,
            {
                generate_signature_assets.STAR_CORE,
                generate_signature_assets.STAR_MID,
                generate_signature_assets.STAR_OUTER,
            },
        )
        glow = master.find(f'.//{self.namespace}filter[@id="starGlow"]')
        self.assertIsNotNone(glow)
        blur = glow.find(f"{self.namespace}feGaussianBlur")
        flood = glow.find(f"{self.namespace}feFlood")
        self.assertIsNotNone(blur)
        self.assertIsNotNone(flood)
        self.assertEqual(blur.get("stdDeviation"), "2.6")
        self.assertEqual(flood.get("flood-color"), "#3b82f6")
        self.assertEqual(flood.get("flood-opacity"), "0.24")

        animated = (
            ROOT / "assets" / "brand" / "kc-lt-signature-animated.svg"
        ).read_text(encoding="utf-8")
        self.assertIn(
            ".signature-star{opacity:0;animation:signatureStarReveal .32s ease-out 1.14s both}",
            animated,
        )
        self.assertIn(
            ".signature-star{animation:none!important;opacity:1!important}",
            animated,
        )
        star_rule = re.search(
            r"\.signature-star\{opacity:0;animation:([^}]+)\}", animated
        )
        self.assertIsNotNone(star_rule)
        self.assertNotIn("infinite", star_rule.group(1))
        pen_end = max(
            float(stroke.delay.removesuffix("s"))
            + float(stroke.duration.removesuffix("s"))
            for stroke in generate_signature_assets.PRIMARY_STROKES
        )
        self.assertAlmostEqual(pen_end, 2.6)
        self.assertLessEqual(1.14 + 0.32, pen_end)

    def test_banner_embeddings_keep_one_compact_star_and_accessible_description(self) -> None:
        for path in generate_signature_assets.BANNER_FILES:
            root = ET.parse(path).getroot()
            ink_groups = root.findall(
                f'.//{self.namespace}g[@class="signature-ink"]'
            )
            stars = root.findall(
                f'.//{self.namespace}g[@class="signature-star"]'
            )
            placements = root.findall(
                f'.//{self.namespace}g[@class="signature-star-placement"]'
            )
            self.assertEqual(len(ink_groups), 1, path.name)
            self.assertEqual(
                len(ink_groups[0].findall(f"./{self.namespace}path")), 8, path.name
            )
            self.assertEqual(len(stars), 1, path.name)
            self.assertEqual(len(placements), 1, path.name)
            self.assertEqual(
                placements[0].get("transform"), "translate(178 94)", path.name
            )
            self.assertIsNone(stars[0].get("transform"), path.name)
            self.assertEqual(stars[0].get("aria-hidden"), "true", path.name)
            description = root.find(f"{self.namespace}desc")
            self.assertIsNotNone(description, path.name)
            self.assertIn("KC star LT", description.text or "", path.name)


class SocialPreviewAssetTests(unittest.TestCase):
    """Keep all GitHub social-preview pairs upload-ready."""

    def test_social_previews_are_exactly_1280_by_640(self) -> None:
        basenames = (
            "profile-social-preview",
            "novamusiclab-social-preview",
            "novafit-social-preview",
            "ivrit-sheli-social-preview",
            "christopherrodriguezcvonline-social-preview",
            "fullstack2026-social-preview",
        )
        for basename in basenames:
            png_path = ROOT / "assets" / "social" / f"{basename}.png"
            png = png_path.read_bytes()
            self.assertGreaterEqual(len(png), 33, png_path.name)
            self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n", png_path.name)
            self.assertEqual(png[12:16], b"IHDR", png_path.name)
            self.assertEqual(struct.unpack(">II", png[16:24]), (1280, 640), png_path.name)

            svg_path = ROOT / "assets" / "social" / f"{basename}.svg"
            root = ET.parse(svg_path).getroot()
            self.assertEqual(root.tag.rsplit("}", 1)[-1], "svg", svg_path.name)
            self.assertEqual(root.get("width"), "1280", svg_path.name)
            self.assertEqual(root.get("height"), "640", svg_path.name)
            self.assertEqual(root.get("viewBox"), "0 0 1280 640", svg_path.name)
            if basename == "christopherrodriguezcvonline-social-preview":
                title = root.find("{http://www.w3.org/2000/svg}title")
                self.assertIsNotNone(title, svg_path.name)
                self.assertIn("Rodríguez", title.text or "", svg_path.name)

    def test_social_previews_reuse_the_canonical_compact_signature(self) -> None:
        """Prevent share-card copies of KC star LT from drifting from the master."""

        signature = ET.parse(
            ROOT / "assets" / "brand" / "kc-lt-signature-compact.svg"
        ).getroot()
        namespace = "{http://www.w3.org/2000/svg}"
        ink = signature.find(f'.//{namespace}g[@class="signature-ink"]')
        self.assertIsNotNone(ink)
        canonical_paths = [
            path.get("d") for path in ink.findall(f"./{namespace}path")
        ]
        self.assertEqual(len(canonical_paths), 8)
        self.assertNotIn(None, canonical_paths)

        for svg_path in sorted((ROOT / "assets" / "social").glob("*.svg")):
            source = svg_path.read_text(encoding="utf-8")
            for path_data in canonical_paths:
                self.assertIn(f'd="{path_data}"', source, svg_path.name)
            root = ET.parse(svg_path).getroot()
            stars = root.findall(f'.//{namespace}g[@class="signature-star"]')
            placements = root.findall(
                f'.//{namespace}g[@class="signature-star-placement"]'
            )
            self.assertEqual(len(stars), 1, svg_path.name)
            self.assertEqual(len(placements), 1, svg_path.name)
            self.assertEqual(
                placements[0].get("transform"), "translate(178 94)", svg_path.name
            )
            self.assertIsNone(stars[0].get("transform"), svg_path.name)
            self.assertEqual(stars[0].get("aria-hidden"), "true", svg_path.name)
            self.assertEqual(stars[0].get("filter"), "url(#signatureStarGlow)")
            description = root.find(f"{namespace}desc")
            self.assertIsNotNone(description, svg_path.name)
            self.assertIn("KC star LT", description.text or "", svg_path.name)

    def test_novafit_secondary_art_uses_verified_4_2_facts(self) -> None:
        """Keep retained cards consistent with the canonical public manifest."""

        targets = (
            ROOT / "assets" / "social" / "novafit-social-preview.svg",
            ROOT / "assets" / "projects" / "novafit.svg",
            ROOT / "assets" / "portfolio-command-center-animated.svg",
            ROOT / "assets" / "portfolio-command-center-static.svg",
            ROOT / "assets" / "portfolio-command-center-mobile.svg",
            ROOT / "assets" / "portfolio-command-center-mobile-static.svg",
            ROOT / "assets" / "self-healing-verification-animated.svg",
        )
        for path in targets:
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("74 tests", source, path.name)
            self.assertNotIn("74 TESTS", source, path.name)
            self.assertNotIn("Ultimate 4.0", source, path.name)

        social = targets[0].read_text(encoding="utf-8")
        self.assertIn("124 tests", social)
        self.assertIn("12 themes", social)
        self.assertIn("v4.2", social)


class ExternalLinkAuditTests(unittest.TestCase):
    """Keep the scheduled link audit deterministic and conservative."""

    def test_extract_urls_deduplicates_public_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "PROFILE.md"
            source.write_text(
                "[one](https://example.com/path)\n"
                '"https://example.com/path"\n'
                "[two](https://example.org/demo/).\n",
                encoding="utf-8",
            )

            self.assertEqual(
                check_external_links.extract_urls([source]),
                ["https://example.com/path", "https://example.org/demo/"],
            )

    def test_status_classification_fails_only_convincing_client_errors(self) -> None:
        self.assertEqual(
            check_external_links.classify_status("https://example.com", 200), "ok"
        )
        self.assertEqual(
            check_external_links.classify_status("https://example.com/missing", 404),
            "failure",
        )
        self.assertEqual(
            check_external_links.classify_status("https://example.com/gone", 410),
            "failure",
        )
        self.assertEqual(
            check_external_links.classify_status("https://example.com/range", 416),
            "warning",
        )
        self.assertEqual(
            check_external_links.classify_status("https://example.com/restricted", 451),
            "warning",
        )
        self.assertEqual(
            check_external_links.classify_status("https://example.com", 429),
            "warning",
        )
        self.assertEqual(
            check_external_links.classify_status("https://www.linkedin.com/in/example", 999),
            "warning",
        )

    def test_get_fallback_can_recover_from_a_rejected_head_request(self) -> None:
        statuses = iter((405, 200))

        class Response:
            def __init__(self, status: int) -> None:
                self.status = status

            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def getcode(self) -> int:
                return self.status

        def opener(*args: object, **kwargs: object) -> Response:
            return Response(next(statuses))

        result = check_external_links.check_url(
            "https://example.com/profile", timeout=1, opener=opener
        )

        self.assertEqual(result.state, "ok")
        self.assertEqual(result.status, 200)
        self.assertIn("HEAD HTTP 405; GET HTTP 200", result.detail)


class GlobeSourceProvenanceTests(unittest.TestCase):
    """Protect checksum verification and offline cache behavior."""

    def test_supplementals_are_only_the_source_missing_sovereigns(self) -> None:
        supplemental = set(generate_world_globe.SUPPLEMENTAL_SOVEREIGN_CENTROIDS)
        source_codes = generate_world_globe.SOVEREIGN_ISO_A3 - supplemental

        source_sovereigns, validated_supplemental = (
            generate_world_globe._validate_sovereign_contract(set(source_codes))
        )

        self.assertEqual(len(source_sovereigns), 182)
        self.assertEqual(validated_supplemental, supplemental)
        with self.assertRaisesRegex(ValueError, r"source-present definitions=\['AND'\]"):
            generate_world_globe._validate_sovereign_contract(
                set(source_codes) | {"AND"}
            )

    def test_feature_codes_prefer_valid_iso_a3_before_adm0_a3(self) -> None:
        self.assertEqual(
            generate_world_globe._feature_iso({"ISO_A3": "PSE", "ADM0_A3": "PSX"}),
            "PSE",
        )
        self.assertEqual(
            generate_world_globe._feature_iso({"ISO_A3": "-99", "ADM0_A3": "FRA"}),
            "FRA",
        )

    def test_verified_cache_supports_offline_generation(self) -> None:
        payload = b'{"type":"FeatureCollection","features":[{"type":"Feature"}]}'
        source = generate_world_globe.SourceSpec(
            filename="countries.geojson",
            url="https://example.com/countries.geojson",
            sha256=hashlib.sha256(payload).hexdigest(),
        )
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            (cache / source.filename).write_bytes(payload)

            data = generate_world_globe.fetch_geojson(source, cache, offline=True)

        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(len(data["features"]), 1)

    def test_corrupt_offline_cache_is_rejected(self) -> None:
        source = generate_world_globe.SourceSpec(
            filename="countries.geojson",
            url="https://example.com/countries.geojson",
            sha256="0" * 64,
        )
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            (cache / source.filename).write_text("{}", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, r"Checksum mismatch"):
                generate_world_globe.fetch_geojson(source, cache, offline=True)


if __name__ == "__main__":
    unittest.main()
