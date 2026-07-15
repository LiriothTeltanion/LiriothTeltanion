"""Regression tests for the manifest-backed NovaFit profile synchronization."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_profile, sync_novafit

ROOT = Path(__file__).resolve().parent.parent


def valid_manifest() -> dict[str, object]:
    """Return a minimal valid NovaFit public project manifest."""
    return {
        "schema": "nova-portfolio-project-v1",
        "slug": "novafit",
        "name": "NovaFit",
        "version": "4.1.0",
        "status": "active",
        "default_branch": "main",
        "repository": "https://github.com/LiriothTeltanion/NovaFit",
        "summary": (
            "A local-first Windows wellness studio with isolated profiles, Hebrew RTL, "
            "efficient motion, explainable analytics and verified backups."
        ),
        "platforms": ["Windows desktop", "Python CLI"],
        "languages": ["en", "es", "he"],
        "theme_count": 12,
        "quality": {
            "workflow": ".github/workflows/quality.yml",
            "automated_tests_discovered": 123,
            "verification_command": "VERIFY_ALL.bat",
            "release_audit": "python tools/package_audit.py --strict-distribution",
        },
        "capabilities": [
            "multi-profile SQLite isolation",
            "Hebrew right-to-left interface",
            "complete all-profile ZIP backups with SHA-256",
        ],
        "privacy": {
            "local_first": True,
            "tracked_runtime_data": False,
            "weather_sends_health_records": False,
        },
        "assets": {
            "count": 27,
            "total_bytes": 1_234_567,
            "hero": "assets/banner.svg",
        },
    }


class NovaFitSyncTests(unittest.TestCase):
    """Keep remote input bounded and generated profile facts deterministic."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))

    def test_manifest_updates_only_the_canonical_novafit_project(self) -> None:
        original = copy.deepcopy(self.profile)

        updated = sync_novafit.apply_manifest(self.profile, valid_manifest())

        original_novafit = next(
            project for project in original["projects"] if project["name"] == "NovaFit"
        )
        updated_novafit = next(
            project for project in updated["projects"] if project["name"] == "NovaFit"
        )
        self.assertEqual(self.profile, original)
        self.assertEqual(updated["identity"], original["identity"])
        self.assertEqual(updated["projects"][0], original["projects"][0])
        self.assertNotEqual(updated_novafit["evidence"], original_novafit["evidence"])
        self.assertEqual(updated_novafit["portfolio_sync"]["version"], "4.1.0")
        self.assertEqual(
            updated_novafit["portfolio_sync"]["automated_tests_discovered"], 123
        )

        readme = build_profile.render_profile(updated, "compact")
        self.assertIn("NovaFit v4.1.0", readme)
        self.assertIn("runs 123 discovered automated tests", readme)
        self.assertIn("Verified project manifest", readme)

    def test_manifest_rejects_identity_and_markdown_injection(self) -> None:
        wrong_repository = valid_manifest()
        wrong_repository["repository"] = "https://github.com/example/other"
        with self.assertRaisesRegex(ValueError, "Unexpected repository URL"):
            sync_novafit.validate_manifest(wrong_repository)

        unsafe_summary = valid_manifest()
        unsafe_summary["summary"] = "Safe first line\nInjected heading"
        with self.assertRaisesRegex(ValueError, "unsafe Markdown"):
            sync_novafit.validate_manifest(unsafe_summary)

        unsafe_capability = valid_manifest()
        unsafe_capability["capabilities"][0] = "<img src=x>"
        with self.assertRaisesRegex(ValueError, "unsafe Markdown"):
            sync_novafit.validate_manifest(unsafe_capability)

    def test_write_then_offline_check_detects_readme_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "profile.json"
            manifest = root / "incoming.json"
            snapshot = root / "snapshot.json"
            compact = root / "README.md"
            expanded = root / "README_EXPANDED.md"
            profile.write_text(
                json.dumps(self.profile, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest.write_text(
                json.dumps(valid_manifest(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            common = [
                "--profile",
                str(profile),
                "--snapshot",
                str(snapshot),
                "--compact-output",
                str(compact),
                "--expanded-output",
                str(expanded),
            ]

            self.assertEqual(
                sync_novafit.main(["--manifest", str(manifest), "--write", *common]),
                0,
            )
            self.assertEqual(
                sync_novafit.main(["--manifest", str(snapshot), "--check", *common]),
                0,
            )
            compact.write_text("stale\n", encoding="utf-8")
            self.assertEqual(
                sync_novafit.main(["--manifest", str(snapshot), "--check", *common]),
                1,
            )

    def test_remote_fetch_rejects_every_noncanonical_url_before_network_access(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "canonical raw GitHub manifest"):
            sync_novafit.fetch_manifest("https://example.com/project.json")


if __name__ == "__main__":
    unittest.main()
