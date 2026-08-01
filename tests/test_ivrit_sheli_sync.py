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
        "schema": "ivrit-sheli-portfolio-project-v2",
        "slug": "ivrit-sheli",
        "name": "Ivrit Sheli — העברית שלי",
        "source_version": "2.4.0",
        "live_version": "2.4.0",
        "status": "production",
        "default_branch": "main",
        "repository_url": "https://github.com/LiriothTeltanion/IvritSheli",
        "demo_url": "https://ivritsheli-production.up.railway.app",
        "summary": (
            "A private-first trilingual Hebrew-learning product with a guided contest "
            "tour, 48 reviewed visual concepts, local SQLite, authenticated PostgreSQL, "
            "native RTL and accessible motion."
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
            "version": "2.4.0",
            "backend_unique": 151,
            "frontend": 62,
            "frontend_files": 16,
            "total_unique": 213,
            "ordinary_backend_passed": 150,
            "ordinary_backend_skipped": 1,
            "postgresql_gate_passed": 3,
            "evidence": "TEST_REPORT.md",
        },
        "deployment": {
            "version": "2.4.0",
            "provider": "Railway",
            "runtime": "Docker",
            "database": "PostgreSQL 17",
            "status": "verified-live",
            "release_implementation_commit": (
                "03bf84b9268ff8be528c0fab3c670f9652ee23b0"
            ),
            "verified_on": "2026-07-21",
            "environment": "production",
            "health_live": True,
            "health_ready": True,
            "postgresql_ready": True,
            "dictionary_ready": True,
            "dictionary_entries": 48,
            "english_entry_verified": True,
            "read_only_tour_verified": True,
        },
        "publication": {
            "latest_git_tag": "v2.4.0",
            "latest_github_release": "v2.4.0",
            "source_version_tagged": True,
            "source_version_github_release_published": True,
            "release_state": "2.4.0-live-and-published",
        },
        "visual_proof": {
            "state": "live-english-journey-verified",
            "social_preview_version": "2.2.0",
            "readme_screenshot_version": "2.1.x",
            "readme_screenshots_match_source_version": False,
            "interactive_browser_qa": (
                "verified-english-entry-and-read-only-tour"
            ),
        },
        "oauth": {
            "providers": ["Google", "GitHub"],
            "source_contract_tested": True,
            "google_live_configured": True,
            "google_live_sign_in_verified": True,
            "github_live_successful_session_verified": False,
            "authenticated_session_refresh_verified": True,
            "onboarding_persistence_across_reload_verified": True,
            "logout_verified": True,
            "signed_out_reload_verified": True,
            "relogin_after_logout_verified": False,
            "boundary": (
                "Identity-only Google sign-in, onboarding/session persistence across "
                "reload, logout and signed-out persistence after reload are verified in "
                "production. Re-login after logout, a live GitHub account session, live "
                "OpenAI or Google Workspace connector calls, two-real-user isolation and "
                "backup restoration remain unverified; Google sign-in grants no Gmail, "
                "Drive or Calendar scope."
            ),
        },
        "privacy": {
            "local_first": True,
            "public_demo_data": "synthetic",
            "public_demo_mutations": "server-blocked",
            "self_service_export_in_source": True,
            "self_service_deletion_in_source": True,
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
        self.assertEqual(updated_ivrit["status"], "Live v2.4.0 dual-mode full-stack product")
        self.assertEqual(updated_ivrit["release_evidence"]["total_tests"], 213)
        self.assertEqual(updated_ivrit["portfolio_sync"]["backend_tests"], 151)
        self.assertEqual(updated_ivrit["portfolio_sync"]["frontend_tests"], 62)
        self.assertTrue(updated_ivrit["portfolio_sync"]["postgresql_ready"])
        self.assertFalse(
            updated_ivrit["portfolio_sync"][
                "github_live_successful_session_verified"
            ]
        )
        self.assertEqual(
            updated_ivrit["portfolio_sync"]["release_state"],
            "2.4.0-live-and-published",
        )
        self.assertEqual(updated_ivrit["media"]["version"], "2.2.0")
        self.assertFalse(updated_ivrit["media"]["current_release_visual_proof"])

        readme = build_profile.render_profile(updated, "compact")
        self.assertIn("151 backend + 62 frontend = 213 passing tests", readme)
        self.assertIn("PostgreSQL 17 ready", readme)
        self.assertIn("interaction history, not visual proof", readme)
        self.assertIn("a live GitHub account session", readme)

    def test_new_live_version_archives_older_profile_media(self) -> None:
        source_profile = copy.deepcopy(self.profile)
        source_ivrit = next(
            project
            for project in source_profile["projects"]
            if project["name"] == "Ivrit Sheli"
        )
        source_ivrit["media"]["current_release_visual_proof"] = True
        self.assertTrue(source_ivrit["media"]["current_release_visual_proof"])

        updated = sync_ivrit_sheli.apply_manifest(source_profile, valid_manifest())
        updated_ivrit = next(
            project for project in updated["projects"] if project["name"] == "Ivrit Sheli"
        )

        self.assertEqual(updated_ivrit["media"]["version"], "2.2.0")
        self.assertFalse(updated_ivrit["media"]["current_release_visual_proof"])
        self.assertIn("not visual proof of the live 2.4.0", updated_ivrit["media"]["alt"])
        self.assertEqual(
            updated_ivrit["portfolio_sync"]["visual_proof_state"],
            "live-english-journey-verified",
        )

    def test_current_upstream_screenshots_do_not_promote_profile_owned_media(self) -> None:
        manifest = valid_manifest()
        manifest["visual_proof"] = {
            "state": "live-english-journey-verified",
            "social_preview_version": "2.2.0",
            "readme_screenshot_version": "2.4.0",
            "readme_screenshots_match_source_version": True,
            "interactive_browser_qa": (
                "verified-english-entry-and-read-only-tour"
            ),
        }

        updated = sync_ivrit_sheli.apply_manifest(self.profile, manifest)
        updated_ivrit = next(
            project for project in updated["projects"] if project["name"] == "Ivrit Sheli"
        )

        self.assertTrue(
            updated_ivrit["portfolio_sync"][
                "readme_screenshots_match_source_version"
            ]
        )
        self.assertFalse(updated_ivrit["media"]["current_release_visual_proof"])
        self.assertEqual(updated_ivrit["media"]["version"], "2.2.0")

    def test_new_same_version_release_commit_expires_profile_captures(self) -> None:
        manifest = valid_manifest()
        reviewed_commit = str(
            manifest["deployment"]["release_implementation_commit"]
        )
        source_profile = copy.deepcopy(self.profile)
        source_ivrit = next(
            project
            for project in source_profile["projects"]
            if project["name"] == "Ivrit Sheli"
        )
        source_ivrit["media"]["version"] = "2.4.0"
        source_ivrit["media"]["captured_release_commit"] = reviewed_commit
        source_ivrit["media"]["current_release_visual_proof"] = True
        manifest["deployment"]["release_implementation_commit"] = "a" * 40

        updated = sync_ivrit_sheli.apply_manifest(source_profile, manifest)
        updated_ivrit = next(
            project for project in updated["projects"] if project["name"] == "Ivrit Sheli"
        )

        self.assertFalse(updated_ivrit["media"]["current_release_visual_proof"])
        self.assertIn("not visual proof", updated_ivrit["media"]["alt"])
        self.assertEqual(
            updated_ivrit["media"]["captured_release_commit"],
            reviewed_commit,
        )

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
        optimistic_oauth["oauth"]["github_live_successful_session_verified"] = True
        with self.assertRaisesRegex(ValueError, "must remain false until explicitly reviewed"):
            sync_ivrit_sheli.validate_manifest(optimistic_oauth)

        optimistic_media = valid_manifest()
        optimistic_media["visual_proof"]["readme_screenshots_match_source_version"] = True
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
            "release_state": "2.4.0-deployment-ahead-of-github-release",
        }

        with self.assertRaisesRegex(ValueError, "regress.*publication state"):
            sync_ivrit_sheli.prevent_publication_regression(reviewed, incoming)

    def test_same_version_remote_cannot_replace_reviewed_release_commit(self) -> None:
        reviewed = sync_ivrit_sheli.validate_manifest(valid_manifest())
        incoming = valid_manifest()
        incoming["deployment"]["release_implementation_commit"] = "b" * 40
        incoming = sync_ivrit_sheli.validate_manifest(incoming)

        with self.assertRaisesRegex(
            ValueError, "reviewed same-version release implementation commit"
        ):
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
        self.assertEqual(
            manifest["publication"]["release_state"],
            "2.4.0-live-and-published",
        )
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

    def test_workflows_detect_drift_without_writing_or_pushing(self) -> None:
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
        self.assertIn(
            'python scripts/sync_ivrit_sheli.py --url "$MANIFEST_URL" --check',
            workflow,
        )
        self.assertIn(
            'python scripts/sync_novafit.py --url "$MANIFEST_URL" --check',
            novafit_workflow,
        )
        self.assertNotIn("secrets.", workflow)
        concurrency = "group: profile-project-sync-${{ github.repository }}"
        self.assertIn(concurrency, workflow)
        self.assertIn(concurrency, novafit_workflow)
        for configured_workflow in (workflow, novafit_workflow):
            self.assertIn("contents: read", configured_workflow)
            self.assertIn("persist-credentials: false", configured_workflow)
            self.assertNotIn("contents: write", configured_workflow)
            self.assertNotIn("--write", configured_workflow)
            self.assertNotIn("git commit", configured_workflow)
            self.assertNotIn("git push", configured_workflow)


if __name__ == "__main__":
    unittest.main()
