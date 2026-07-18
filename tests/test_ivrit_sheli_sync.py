"""Regression tests for manifest-backed Ivrit Sheli profile synchronization."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_profile, sync_ivrit_sheli

ROOT = Path(__file__).resolve().parent.parent


def valid_manifest() -> dict[str, object]:
    """Return the complete current Ivrit Sheli public manifest contract."""
    return {
        "schema": "ivrit-sheli-portfolio-project-v1",
        "slug": "ivrit-sheli",
        "name": "Ivrit Sheli — העברית שלי",
        "source_version": "2.2.0",
        "live_version": "2.2.0",
        "status": "live",
        "default_branch": "main",
        "repository_url": "https://github.com/LiriothTeltanion/IvritSheli",
        "demo_url": "https://ivritsheli-production.up.railway.app",
        "summary": (
            "A private-first trilingual Hebrew-learning product with local SQLite, "
            "authenticated PostgreSQL, native RTL, accessible motion and a synthetic "
            "read-only public demo."
        ),
        "languages": ["en", "es", "he"],
        "stack": [
            "React 19",
            "TypeScript",
            "FastAPI",
            "Python",
            "PostgreSQL 17",
            "SQLite",
            "Docker",
            "Railway",
        ],
        "tests": {
            "backend_unique": 139,
            "frontend": 48,
            "frontend_files": 12,
            "total_unique": 187,
            "ordinary_backend_passed": 138,
            "ordinary_backend_skipped": 1,
            "postgresql_gate_passed": 3,
            "evidence": "TEST_REPORT.md",
        },
        "deployment": {
            "provider": "Railway",
            "runtime": "Docker",
            "database": "PostgreSQL 17",
            "status": "verified",
            "production_commit": "c8c928661bdcf179ed1d9df88b9f2e4d730ffea3",
            "verified_on": "2026-07-18",
            "environment": "production",
            "health_live": True,
            "health_ready": True,
            "postgresql_ready": True,
            "dictionary_ready": True,
        },
        "publication": {
            "latest_git_tag": "v2.2.0",
            "latest_github_release": "v2.2.0",
            "source_version_tagged": True,
            "source_version_github_release_published": True,
            "release_state": "published-and-deployed",
        },
        "visual_proof": {
            "state": "partial",
            "social_preview_version": "2.2.0",
            "readme_screenshot_version": "2.1.x",
            "readme_screenshots_match_live_version": False,
            "live_2_2_interactive_browser_qa": "pending",
        },
        "oauth": {
            "provider": "GitHub",
            "consent_handoff_verified": True,
            "cancellation_verified": True,
            "final_live_code_exchange_verified": False,
            "authenticated_session_refresh_verified": False,
            "logout_verified": False,
            "boundary": (
                "Consent handoff and cancellation are verified; the final live "
                "authorization-code exchange, authenticated refresh persistence and "
                "logout are not verified end to end."
            ),
        },
        "privacy": {
            "local_first": True,
            "public_demo_data": "synthetic",
            "public_demo_mutations": "server-blocked",
            "contains_secrets": False,
        },
    }


class IvritSheliSyncTests(unittest.TestCase):
    """Keep remote evidence bounded, conservative and deterministic."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))

    def test_manifest_updates_only_the_canonical_ivrit_project(self) -> None:
        source_profile = copy.deepcopy(self.profile)
        source_ivrit = next(
            project
            for project in source_profile["projects"]
            if project["name"] == "Ivrit Sheli"
        )
        source_ivrit["solution"] = "Deliberately stale Ivrit portfolio summary."
        original = copy.deepcopy(source_profile)

        updated = sync_ivrit_sheli.apply_manifest(source_profile, valid_manifest())

        original_ivrit = next(
            project for project in original["projects"] if project["name"] == "Ivrit Sheli"
        )
        updated_ivrit = next(
            project for project in updated["projects"] if project["name"] == "Ivrit Sheli"
        )
        self.assertEqual(source_profile, original)
        self.assertEqual(updated["identity"], original["identity"])
        self.assertEqual(updated["projects"][0], original["projects"][0])
        self.assertEqual(updated["projects"][2:], original["projects"][2:])
        self.assertNotEqual(updated_ivrit["solution"], original_ivrit["solution"])
        self.assertEqual(updated_ivrit["status"], "Live v2.2.0 dual-mode full-stack product")
        self.assertEqual(updated_ivrit["release_evidence"]["total_tests"], 187)
        self.assertEqual(updated_ivrit["portfolio_sync"]["backend_tests"], 139)
        self.assertEqual(updated_ivrit["portfolio_sync"]["frontend_tests"], 48)
        self.assertTrue(updated_ivrit["portfolio_sync"]["postgresql_ready"])
        self.assertFalse(
            updated_ivrit["portfolio_sync"]["oauth_final_live_code_exchange_verified"]
        )
        self.assertEqual(
            updated_ivrit["portfolio_sync"]["release_state"],
            "published-and-deployed",
        )
        self.assertEqual(updated_ivrit["media"]["version"], "2.1.x")
        self.assertFalse(updated_ivrit["media"]["current_release_visual_proof"])

        readme = build_profile.render_profile(updated, "compact")
        self.assertIn("139 backend + 48 frontend = 187 passing tests", readme)
        self.assertIn("PostgreSQL 17 ready", readme)
        self.assertIn("not visual proof of the live 2.2.0 interface", readme)
        self.assertIn("final live authorization-code exchange", readme)

    def test_manifest_rejects_unknown_fields_injection_and_identity_drift(self) -> None:
        extra = valid_manifest()
        extra["unreviewed"] = "claim"
        with self.assertRaisesRegex(ValueError, "unexpected unreviewed"):
            sync_ivrit_sheli.validate_manifest(extra)

        wrong_repository = valid_manifest()
        wrong_repository["repository_url"] = "https://github.com/example/other"
        with self.assertRaisesRegex(ValueError, "Unexpected repository URL"):
            sync_ivrit_sheli.validate_manifest(wrong_repository)

        unsafe_summary = valid_manifest()
        unsafe_summary["summary"] = "Safe first line\nInjected heading"
        with self.assertRaisesRegex(ValueError, "unsafe Markdown"):
            sync_ivrit_sheli.validate_manifest(unsafe_summary)

        wrong_demo = valid_manifest()
        wrong_demo["demo_url"] = "https://example.com"
        with self.assertRaisesRegex(ValueError, "Unexpected live demo URL"):
            sync_ivrit_sheli.validate_manifest(wrong_demo)

    def test_manifest_rejects_arithmetic_readiness_and_optimistic_oauth(self) -> None:
        wrong_total = valid_manifest()
        wrong_total["tests"]["total_unique"] = 188
        with self.assertRaisesRegex(ValueError, "Total tests must equal"):
            sync_ivrit_sheli.validate_manifest(wrong_total)

        unready = valid_manifest()
        unready["deployment"]["postgresql_ready"] = False
        with self.assertRaisesRegex(ValueError, "postgresql_ready must be true"):
            sync_ivrit_sheli.validate_manifest(unready)

        optimistic_oauth = valid_manifest()
        optimistic_oauth["oauth"]["final_live_code_exchange_verified"] = True
        with self.assertRaisesRegex(ValueError, "must remain false until verified"):
            sync_ivrit_sheli.validate_manifest(optimistic_oauth)

        optimistic_media = valid_manifest()
        optimistic_media["visual_proof"]["readme_screenshots_match_live_version"] = True
        optimistic_media["visual_proof"]["state"] = "partial"
        with self.assertRaisesRegex(ValueError, "Screenshots marked current"):
            sync_ivrit_sheli.validate_manifest(optimistic_media)

    def test_same_version_remote_cannot_regress_reviewed_publication(self) -> None:
        reviewed = sync_ivrit_sheli.validate_manifest(valid_manifest())
        incoming = valid_manifest()
        incoming["publication"] = {
            "latest_git_tag": "v2.1.0",
            "latest_github_release": "v2.1.0",
            "source_version_tagged": False,
            "source_version_github_release_published": False,
            "release_state": "deployment-ahead-of-github-release",
        }
        incoming = sync_ivrit_sheli.validate_manifest(incoming)

        with self.assertRaisesRegex(ValueError, "regress.*publication state"):
            sync_ivrit_sheli.prevent_publication_regression(reviewed, incoming)

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
                sync_ivrit_sheli.main(
                    ["--manifest", str(manifest), "--write", *common]
                ),
                0,
            )
            self.assertEqual(
                sync_ivrit_sheli.main(
                    ["--manifest", str(snapshot), "--check", *common]
                ),
                0,
            )
            compact.write_text("stale\n", encoding="utf-8")
            self.assertEqual(
                sync_ivrit_sheli.main(
                    ["--manifest", str(snapshot), "--check", *common]
                ),
                1,
            )

    def test_remote_fetch_rejects_noncanonical_url_before_network_access(self) -> None:
        with self.assertRaisesRegex(ValueError, "canonical raw GitHub manifest"):
            sync_ivrit_sheli.fetch_manifest("https://example.com/project.json")

    def test_remote_fetch_bypasses_stale_raw_content_cache(self) -> None:
        payload = json.dumps(valid_manifest(), ensure_ascii=False).encode("utf-8")
        captured: dict[str, object] = {}

        class Response:
            headers = {"Content-Length": str(len(payload))}

            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self, limit: int) -> bytes:
                self.assert_limit(limit)
                return payload

            @staticmethod
            def assert_limit(limit: int) -> None:
                if limit != sync_ivrit_sheli.MAX_MANIFEST_BYTES + 1:
                    raise AssertionError("Manifest read must remain size-bounded.")

        def fake_urlopen(request: object, timeout: float) -> Response:
            captured["request"] = request
            captured["timeout"] = timeout
            return Response()

        with patch.object(sync_ivrit_sheli, "urlopen", fake_urlopen):
            manifest = sync_ivrit_sheli.fetch_manifest(
                sync_ivrit_sheli.DEFAULT_MANIFEST_URL
            )

        request = captured["request"]
        self.assertEqual(manifest["publication"]["release_state"], "published-and-deployed")
        self.assertEqual(
            request.get_header("Cache-control"),
            "no-cache, no-store, max-age=0",
        )
        self.assertEqual(request.get_header("Pragma"), "no-cache")
        self.assertTrue(request.get_header("User-agent").startswith("Lirioth-profile-sync/"))
        self.assertTrue(
            request.full_url.startswith(
                f"{sync_ivrit_sheli.DEFAULT_MANIFEST_URL}?profile-sync="
            )
        )

    def test_workflow_has_safe_bootstrap_and_serialized_generated_writes(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "sync-ivrit-sheli.yml"
        ).read_text(encoding="utf-8")
        novafit_workflow = (
            ROOT / ".github" / "workflows" / "sync-novafit.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(sync_ivrit_sheli.DEFAULT_MANIFEST_URL, workflow)
        self.assertIn("error.code != 404", workflow)
        self.assertIn("validating the reviewed local snapshot only", workflow)
        self.assertIn("python scripts/sync_ivrit_sheli.py --check", workflow)
        self.assertIn("if: steps.upstream.outputs.available == 'true'", workflow)
        self.assertIn("data/project-snapshots/ivrit-sheli.json", workflow)
        self.assertNotIn("secrets.", workflow)
        concurrency = "group: profile-project-sync-${{ github.repository }}"
        self.assertIn(concurrency, workflow)
        self.assertIn(concurrency, novafit_workflow)


if __name__ == "__main__":
    unittest.main()
