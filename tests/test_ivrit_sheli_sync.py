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
    """Return the reviewed Ivrit Sheli manifest as the fixture baseline.

    This used to be a literal copy of the contract, which is how the fixture
    quietly aged into a shape the project had already left behind. Reading the
    reviewed snapshot keeps the tests measuring the contract that is actually
    in force, without reaching the network.
    """
    return json.loads(
        (ROOT / "data" / "project-snapshots" / "ivrit-sheli.json").read_text(
            encoding="utf-8"
        )
    )


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
        manifest = valid_manifest()
        self.assertEqual(
            updated_ivrit["status"],
            build_profile.ivrit_status_line(
                manifest["source_version"],
                manifest["source_status"],
                manifest["durable_demo"]["status"],
                manifest["durable_demo"]["provider"],
            ),
        )
        self.assertEqual(
            updated_ivrit["release_evidence"]["total_tests"],
            manifest["tests"]["total_unique"],
        )
        self.assertEqual(
            updated_ivrit["portfolio_sync"]["backend_tests"],
            manifest["tests"]["backend_unique"],
        )
        self.assertEqual(
            updated_ivrit["portfolio_sync"]["frontend_tests"],
            manifest["tests"]["frontend"],
        )
        self.assertTrue(updated_ivrit["portfolio_sync"]["demo_currently_available"])
        self.assertFalse(
            updated_ivrit["portfolio_sync"][
                "github_successful_session_verified_at_release"
            ]
        )
        self.assertEqual(
            updated_ivrit["portfolio_sync"]["release_state"],
            manifest["publication"]["release_state"],
        )
        self.assertEqual(updated_ivrit["media"]["version"], "2.2.0")
        self.assertFalse(updated_ivrit["media"]["current_release_visual_proof"])

        readme = build_profile.render_profile(updated, "compact")
        tests = manifest["tests"]
        self.assertIn(
            f"{tests['backend_unique']} backend + {tests['frontend']} frontend = "
            f"{tests['total_unique']} tests",
            readme,
        )
        self.assertIn(manifest["durable_demo"]["provider"], readme)
        self.assertIn("interaction history, not visual proof", readme)
        self.assertIn("a live GitHub session", readme)

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

        manifest = valid_manifest()
        self.assertEqual(updated_ivrit["media"]["version"], "2.2.0")
        self.assertFalse(updated_ivrit["media"]["current_release_visual_proof"])
        self.assertIn(
            f"not visual proof of the {manifest['source_version']}",
            updated_ivrit["media"]["alt"],
        )
        self.assertEqual(
            updated_ivrit["portfolio_sync"]["visual_proof_state"],
            manifest["visual_proof"]["state"],
        )

    def test_current_upstream_screenshots_do_not_promote_profile_owned_media(self) -> None:
        manifest = valid_manifest()
        manifest["visual_proof"] = {
            "state": "Upstream screenshots are current for the reviewed source.",
            "social_preview_version": "2.2.0",
            "readme_screenshot_source_version": manifest["source_version"],
            "readme_screenshot_status": "verified-current",
            "interactive_browser_qa": "Reviewed browser pass over the candidate.",
        }

        updated = sync_ivrit_sheli.apply_manifest(self.profile, manifest)
        updated_ivrit = next(
            project for project in updated["projects"] if project["name"] == "Ivrit Sheli"
        )

        self.assertEqual(
            updated_ivrit["portfolio_sync"]["readme_screenshot_status"],
            "verified-current",
        )
        self.assertFalse(updated_ivrit["media"]["current_release_visual_proof"])
        self.assertEqual(updated_ivrit["media"]["version"], "2.2.0")

    def test_profile_media_stay_current_only_for_the_synchronized_version(self) -> None:
        manifest = valid_manifest()
        source_profile = copy.deepcopy(self.profile)
        source_ivrit = next(
            project
            for project in source_profile["projects"]
            if project["name"] == "Ivrit Sheli"
        )
        reviewed_commit = str(source_ivrit["media"]["captured_release_commit"])
        source_ivrit["media"]["version"] = manifest["source_version"]
        source_ivrit["media"]["current_release_visual_proof"] = True

        updated = sync_ivrit_sheli.apply_manifest(source_profile, manifest)
        updated_ivrit = next(
            project for project in updated["projects"] if project["name"] == "Ivrit Sheli"
        )
        self.assertTrue(updated_ivrit["media"]["current_release_visual_proof"])

        stale_profile = copy.deepcopy(source_profile)
        stale_ivrit = next(
            project
            for project in stale_profile["projects"]
            if project["name"] == "Ivrit Sheli"
        )
        stale_ivrit["media"]["version"] = "2.2.0"

        archived = sync_ivrit_sheli.apply_manifest(stale_profile, manifest)
        archived_ivrit = next(
            project for project in archived["projects"] if project["name"] == "Ivrit Sheli"
        )
        self.assertFalse(archived_ivrit["media"]["current_release_visual_proof"])
        self.assertIn("not visual proof", archived_ivrit["media"]["alt"])
        self.assertEqual(
            archived_ivrit["media"]["captured_release_commit"], reviewed_commit
        )

    def test_manifest_rejects_unknown_fields_injection_and_identity_drift(self) -> None:
        tolerated = valid_manifest()
        tolerated["unreviewed"] = "claim"
        sync_ivrit_sheli.validate_manifest(tolerated)

        incomplete = valid_manifest()
        del incomplete["durable_demo"]
        with self.assertRaisesRegex(ValueError, "missing required fields: durable_demo"):
            sync_ivrit_sheli.validate_manifest(incomplete)

        wrong_repository = valid_manifest()
        wrong_repository["repository_url"] = "https://github.com/example/other"
        with self.assertRaisesRegex(ValueError, "Unexpected repository URL"):
            sync_ivrit_sheli.validate_manifest(wrong_repository)

        unsafe_summary = valid_manifest()
        unsafe_summary["summary"] = "Safe first line\nInjected heading"
        with self.assertRaisesRegex(ValueError, "unsafe Markdown"):
            sync_ivrit_sheli.validate_manifest(unsafe_summary)

        retired_demo = valid_manifest()
        retired_demo["durable_demo"]["url"] = retired_demo["historical_deployment"][
            "former_demo_url"
        ]
        with self.assertRaisesRegex(ValueError, "retired deployment URL"):
            sync_ivrit_sheli.validate_manifest(retired_demo)

    def test_manifest_rejects_arithmetic_readiness_and_optimistic_oauth(self) -> None:
        wrong_total = valid_manifest()
        wrong_total["tests"]["total_unique"] = 188
        with self.assertRaisesRegex(ValueError, "Total tests must equal"):
            sync_ivrit_sheli.validate_manifest(wrong_total)

        unreachable = valid_manifest()
        unreachable["privacy"]["durable_demo_currently_available"] = False
        with self.assertRaisesRegex(ValueError, "marked currently available"):
            sync_ivrit_sheli.validate_manifest(unreachable)

        unknown_state = valid_manifest()
        unknown_state["durable_demo"]["status"] = "probably-fine"
        with self.assertRaisesRegex(ValueError, "refusing to label it"):
            sync_ivrit_sheli.validate_manifest(unknown_state)

        optimistic_release = valid_manifest()
        optimistic_release["publication"]["source_version_tagged"] = True
        with self.assertRaisesRegex(ValueError, "must be both, at that version"):
            sync_ivrit_sheli.validate_manifest(optimistic_release)

    def test_same_version_remote_cannot_regress_reviewed_publication(self) -> None:
        reviewed = sync_ivrit_sheli.validate_manifest(valid_manifest())
        incoming = valid_manifest()
        incoming["durable_demo"]["status"] = "unavailable"
        incoming["privacy"]["durable_demo_currently_available"] = False

        with self.assertRaisesRegex(ValueError, "downgrade.*demo state"):
            sync_ivrit_sheli.prevent_publication_regression(reviewed, incoming)

    def test_same_version_remote_cannot_replace_reviewed_release_commit(self) -> None:
        reviewed = sync_ivrit_sheli.validate_manifest(valid_manifest())
        incoming = valid_manifest()
        incoming["historical_deployment"]["release_implementation_commit"] = "b" * 40
        incoming = sync_ivrit_sheli.validate_manifest(incoming)

        with self.assertRaisesRegex(
            ValueError, "reviewed release implementation commit"
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
            valid_manifest()["publication"]["release_state"],
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
