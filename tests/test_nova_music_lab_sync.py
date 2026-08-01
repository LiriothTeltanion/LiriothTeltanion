"""Regression tests for review-gated Nova Music Lab profile media sync."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from scripts import sync_nova_music_lab


def png(width: int, height: int) -> bytes:
    """Build a small valid RGBA PNG without third-party image libraries."""
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    pixels = b"".join(b"\x00" + (b"\x00\x00\x00\xff" * width) for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk("IHDR".encode(), struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(pixels, level=9))
        + chunk(b"IEND", b"")
    )


PNG_1X1 = png(1, 1)
SOCIAL_PNG = png(1280, 640)
GIF_1X1 = base64.b64decode(
    "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
)
COMMIT = "0123456789abcdef0123456789abcdef01234567"
ROOT = Path(__file__).resolve().parent.parent
TRACKED_CANDIDATE_URL = (
    "https://raw.githubusercontent.com/LiriothTeltanion/NovaMusicLab/"
    "main/public/release-profile-manifest.json"
)


def valid_bundle(
    *,
    status: str = "deployed",
    commit: str | None = COMMIT,
) -> tuple[dict[str, object], dict[str, bytes]]:
    """Return a complete contract plus matching deterministic media bytes."""
    paths = {
        "profile-hero-desktop": (
            "assets/releases/v1.5.0/profile-hero-desktop.png",
            PNG_1X1,
        ),
        "profile-hero-mobile": (
            "assets/releases/v1.5.0/profile-hero-mobile.png",
            PNG_1X1,
        ),
        "profile-tour": (
            "assets/releases/v1.5.0/profile-tour.gif",
            GIF_1X1,
        ),
        "profile-tour-static": (
            "assets/releases/v1.5.0/profile-tour-static.png",
            PNG_1X1,
        ),
        "social-preview": (
            "assets/releases/v1.5.0/social-preview.png",
            SOCIAL_PNG,
        ),
    }
    media = []
    blobs: dict[str, bytes] = {}
    for media_id, (path, payload) in paths.items():
        dimensions = (1280, 640) if media_id == "social-preview" else (1, 1)
        blobs[path] = payload
        media.append(
            {
                "id": media_id,
                "path": path,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "width": dimensions[0],
                "height": dimensions[1],
                "bytes": len(payload),
                "lang": "multilingual",
                "theme": "nova-dark",
                "viewport": {
                    "width": 1440 if media_id.endswith("desktop") else 390,
                    "height": 900 if media_id.endswith("desktop") else 844,
                },
            }
        )
    manifest: dict[str, object] = {
        "schema": "nova-music-profile-release-v1",
        "repository": "LiriothTeltanion/NovaMusicLab",
        "default_branch": "main",
        "live_url": "https://liriothteltanion.github.io/NovaMusicLab/",
        "release": {
            "status": status,
            "version": "1.5.0",
            "commit": commit,
            "captured_on": "2026-08-01",
            "deployed_on": "2026-08-01" if status == "deployed" else None,
        },
        "media": media,
    }
    return manifest, blobs


class StubHttpResponse:
    """Small context-manager response used to inspect outbound requests."""

    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.headers = {"Content-Length": str(len(payload))}

    def __enter__(self) -> "StubHttpResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, amount: int = -1) -> bytes:
        return self.payload if amount < 0 else self.payload[:amount]


class NovaMusicLabSyncTests(unittest.TestCase):
    """Keep candidate generation local, immutable and evidence-linked."""

    def test_manifest_requires_deployed_identity_and_complete_profile_media(
        self,
    ) -> None:
        manifest, _ = valid_bundle()
        validated = sync_nova_music_lab.validate_manifest(manifest)
        self.assertEqual(validated["release"]["version"], "1.5.0")
        self.assertEqual(
            {item["id"] for item in validated["media"]},
            sync_nova_music_lab.REQUIRED_MEDIA_IDS,
        )

        wrong_repository = copy.deepcopy(manifest)
        wrong_repository["repository"] = "https://github.com/example/music"
        with self.assertRaisesRegex(ValueError, "Unexpected repository"):
            sync_nova_music_lab.validate_manifest(wrong_repository)

        missing_tour = copy.deepcopy(manifest)
        missing_tour["media"] = [
            item for item in missing_tour["media"] if item["id"] != "profile-tour"
        ]
        with self.assertRaisesRegex(ValueError, "profile-tour"):
            sync_nova_music_lab.validate_manifest(missing_tour)

        traversal = copy.deepcopy(manifest)
        traversal["media"][0]["path"] = "../private-export.png"
        with self.assertRaisesRegex(ValueError, "unsafe path segment"):
            sync_nova_music_lab.validate_manifest(traversal)

        candidate_with_deployment = copy.deepcopy(manifest)
        candidate_with_deployment["release"]["status"] = "private-candidate"
        with self.assertRaisesRegex(ValueError, "cannot claim deployed_on"):
            sync_nova_music_lab.validate_manifest(candidate_with_deployment)

    def test_manifest_dates_must_be_real_calendar_dates(self) -> None:
        manifest, _ = valid_bundle()
        impossible_date = copy.deepcopy(manifest)
        impossible_date["release"]["deployed_on"] = "2026-02-30"
        with self.assertRaisesRegex(ValueError, "real calendar date"):
            sync_nova_music_lab.validate_manifest(impossible_date)

        impossible_month = copy.deepcopy(manifest)
        impossible_month["release"]["captured_on"] = "2026-13-01"
        with self.assertRaisesRegex(ValueError, "real calendar date"):
            sync_nova_music_lab.validate_manifest(impossible_month)

    def test_media_bytes_hash_and_dimensions_are_all_verified(self) -> None:
        raw_manifest, blobs = valid_bundle()
        manifest = sync_nova_music_lab.validate_manifest(raw_manifest)
        sync_nova_music_lab.verify_media(manifest, blobs)

        corrupted = dict(blobs)
        path = manifest["media"][0]["path"]
        corrupted[path] = corrupted[path] + b"x"
        with self.assertRaisesRegex(ValueError, "byte count"):
            sync_nova_music_lab.verify_media(manifest, corrupted)

        wrong_dimensions = copy.deepcopy(manifest)
        wrong_dimensions["media"][0]["width"] = 2
        with self.assertRaisesRegex(ValueError, "dimensions"):
            sync_nova_music_lab.verify_media(wrong_dimensions, blobs)

    def test_write_stages_ignored_candidate_and_refuses_main(self) -> None:
        raw_manifest, blobs = valid_bundle()
        manifest = sync_nova_music_lab.validate_manifest(raw_manifest)
        with tempfile.TemporaryDirectory() as directory:
            candidate_root = Path(directory) / "candidates"
            candidate_dir, changed = sync_nova_music_lab.stage_candidate(
                manifest,
                blobs,
                candidate_root=candidate_root,
                branch="codex/nova-music-1.5-profile-review",
            )
            self.assertGreaterEqual(len(changed), 5)
            self.assertTrue((candidate_dir / "candidate-plan.json").is_file())
            self.assertTrue(
                (
                    candidate_dir
                    / "media"
                    / "profile-hero-desktop.png"
                ).is_file()
            )
            plan = json.loads(
                (candidate_dir / "candidate-plan.json").read_text(encoding="utf-8")
            )
            self.assertFalse(plan["publication_authorized"])
            self.assertTrue(plan["profile_version_unchanged"])
            self.assertEqual(
                plan["portfolio_sync"]["commit"],
                COMMIT,
            )

            _, unchanged = sync_nova_music_lab.stage_candidate(
                manifest,
                blobs,
                candidate_root=candidate_root,
                branch="codex/nova-music-1.5-profile-review",
            )
            self.assertEqual(unchanged, [])

            with self.assertRaisesRegex(ValueError, "forbidden"):
                sync_nova_music_lab.stage_candidate(
                    manifest,
                    blobs,
                    candidate_root=candidate_root,
                    branch="main",
                )

        candidate, candidate_blobs = valid_bundle(
            status="private-candidate",
            commit=None,
        )
        validated_candidate = sync_nova_music_lab.validate_manifest(candidate)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "only deployed"):
                sync_nova_music_lab.stage_candidate(
                    validated_candidate,
                    candidate_blobs,
                    candidate_root=Path(directory),
                    branch="codex/review",
                )

    def test_read_only_audit_detects_snapshot_media_and_profile_drift(self) -> None:
        raw_manifest, blobs = valid_bundle()
        manifest = sync_nova_music_lab.validate_manifest(raw_manifest)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = root / "snapshot.json"
            profile = root / "profile.json"

            missing = sync_nova_music_lab.audit_reviewed_state(
                manifest,
                blobs,
                snapshot_path=snapshot,
                profile_path=profile,
                profile_root=root,
            )
            self.assertEqual(len(missing), 1)
            self.assertIn("snapshot is missing", missing[0])
            self.assertFalse((root / ".cache").exists())

            snapshot.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            targets = sync_nova_music_lab.profile_targets(manifest)
            by_id = {item["id"]: item for item in manifest["media"]}
            for media_id, relative_target in targets.items():
                target = root / relative_target
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(blobs[by_id[media_id]["path"]])
            readme_references = "\n".join(
                f"./{relative_target}"
                for media_id, relative_target in targets.items()
                if media_id != "social-preview"
            )
            for readme_name in ("README.md", "README_EXPANDED.md"):
                (root / readme_name).write_text(
                    readme_references + "\n",
                    encoding="utf-8",
                )
            profile.write_text(
                json.dumps(
                    {
                        "projects": [
                            {
                                "name": "Nova Music Lab",
                                "source": sync_nova_music_lab.EXPECTED_REPOSITORY_URL,
                                "portfolio_sync": (
                                    sync_nova_music_lab.expected_profile_sync(manifest)
                                ),
                            }
                        ]
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                sync_nova_music_lab.audit_reviewed_state(
                    manifest,
                    blobs,
                    snapshot_path=snapshot,
                    profile_path=profile,
                    profile_root=root,
                ),
                [],
            )

            (root / targets["profile-hero-mobile"]).write_bytes(b"stale")
            stale = sync_nova_music_lab.audit_reviewed_state(
                manifest,
                blobs,
                snapshot_path=snapshot,
                profile_path=profile,
                profile_root=root,
            )
            self.assertIn(
                f"profile media is stale: {targets['profile-hero-mobile']}",
                stale,
            )

            (root / targets["profile-hero-mobile"]).write_bytes(
                blobs[by_id["profile-hero-mobile"]["path"]]
            )
            (root / "README.md").write_text(
                readme_references.replace(
                    f"./{targets['profile-tour']}",
                    "",
                )
                + "\n",
                encoding="utf-8",
            )
            unreferenced = sync_nova_music_lab.audit_reviewed_state(
                manifest,
                blobs,
                snapshot_path=snapshot,
                profile_path=profile,
                profile_root=root,
            )
            self.assertIn(
                (
                    "README.md does not reference current profile-tour: "
                    f"{targets['profile-tour']}"
                ),
                unreferenced,
            )

    def test_local_commit_verification_pins_package_version_and_media(self) -> None:
        raw_manifest, blobs = valid_bundle()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(
                ["git", "-C", str(root), "config", "user.email", "test@example.com"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "user.name", "Test"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "remote",
                    "add",
                    "origin",
                    "https://github.com/LiriothTeltanion/NovaMusicLab.git",
                ],
                check=True,
            )
            (root / "package.json").write_text(
                '{"version":"1.5.0"}\n',
                encoding="utf-8",
            )
            for path, payload in blobs.items():
                destination = root / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(root), "commit", "-q", "-m", "release media"],
                check=True,
            )
            commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            ).stdout.strip()
            raw_manifest["release"]["commit"] = commit
            manifest = sync_nova_music_lab.validate_manifest(raw_manifest)
            committed = sync_nova_music_lab._load_local_commit_bundle(root, manifest)
            sync_nova_music_lab.verify_media(manifest, committed)

            wrong_version = copy.deepcopy(manifest)
            wrong_version["release"]["version"] = "1.5.1"
            with self.assertRaisesRegex(ValueError, "package.json version"):
                sync_nova_music_lab._load_local_commit_bundle(root, wrong_version)

    def test_remote_package_and_media_are_loaded_from_the_deployed_commit(
        self,
    ) -> None:
        raw_manifest, blobs = valid_bundle()
        manifest = sync_nova_music_lab.validate_manifest(raw_manifest)
        raw_base = (
            "https://raw.githubusercontent.com/LiriothTeltanion/NovaMusicLab/"
            f"{COMMIT}/"
        )

        def fake_fetch(url: str, _limit: int, _timeout: float) -> bytes:
            if url == f"{raw_base}package.json":
                return b'{"version":"1.5.0"}\n'
            path = url.removeprefix(raw_base)
            return blobs[path]

        with patch.object(
            sync_nova_music_lab,
            "_fetch_bytes",
            side_effect=fake_fetch,
        ) as mocked_fetch:
            fetched = sync_nova_music_lab._load_remote_commit_bundle(manifest)

        sync_nova_music_lab.verify_media(manifest, fetched)
        fetched_urls = [call.args[0] for call in mocked_fetch.call_args_list]
        self.assertEqual(fetched_urls[0], f"{raw_base}package.json")
        self.assertTrue(all(url.startswith(raw_base) for url in fetched_urls))
        self.assertFalse(any("/main/" in url for url in fetched_urls))

    def test_live_fetch_is_cache_bypassed_and_distinct_from_tracked_candidate(
        self,
    ) -> None:
        deployed, _ = valid_bundle()
        payload = json.dumps(deployed).encode("utf-8")
        with (
            patch.object(sync_nova_music_lab, "time_ns", return_value=123456789),
            patch.object(
                sync_nova_music_lab,
                "urlopen",
                return_value=StubHttpResponse(payload),
            ) as mocked_open,
        ):
            manifest = sync_nova_music_lab.fetch_manifest(
                sync_nova_music_lab.DEFAULT_MANIFEST_URL
            )

        self.assertEqual(manifest["release"]["status"], "deployed")
        self.assertEqual(
            sync_nova_music_lab.expected_profile_sync(manifest)["source"],
            sync_nova_music_lab.DEFAULT_MANIFEST_URL,
        )
        request = mocked_open.call_args.args[0]
        parsed = urlsplit(request.full_url)
        self.assertEqual(parsed.hostname, "liriothteltanion.github.io")
        self.assertEqual(parse_qs(parsed.query), {"profile-sync": ["123456789"]})
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers["cache-control"], "no-cache")
        self.assertEqual(headers["pragma"], "no-cache")

        candidate = copy.deepcopy(deployed)
        candidate["release"]["status"] = "private-candidate"
        candidate["release"]["commit"] = None
        candidate["release"]["deployed_on"] = None
        with tempfile.TemporaryDirectory() as directory:
            candidate_path = Path(directory) / "tracked-candidate.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            loaded_candidate = sync_nova_music_lab.load_manifest(candidate_path)
        self.assertEqual(loaded_candidate["release"]["status"], "private-candidate")

        candidate_payload = json.dumps(candidate).encode("utf-8")
        with patch.object(
            sync_nova_music_lab,
            "urlopen",
            return_value=StubHttpResponse(candidate_payload),
        ):
            with self.assertRaisesRegex(ValueError, "tracked private candidate"):
                sync_nova_music_lab.fetch_manifest(
                    sync_nova_music_lab.DEFAULT_MANIFEST_URL
                )

        with self.assertRaisesRegex(ValueError, "canonical live deployed manifest"):
            sync_nova_music_lab.fetch_manifest(TRACKED_CANDIDATE_URL)

    def test_manual_workflow_is_read_only_and_never_runs_write_mode(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "sync-nova-music-lab.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("git diff --exit-code", workflow)
        self.assertNotIn("--write", workflow)
        self.assertNotIn("git push", workflow)
        self.assertNotIn("pull-requests: write", workflow)

    def test_cli_candidate_root_cannot_escape_ignored_cache(self) -> None:
        sync_nova_music_lab._validate_candidate_root(
            sync_nova_music_lab.DEFAULT_CANDIDATE_ROOT
        )
        with self.assertRaisesRegex(ValueError, "ignored .cache"):
            sync_nova_music_lab._validate_candidate_root(
                sync_nova_music_lab.ROOT / "assets"
            )


if __name__ == "__main__":
    unittest.main()
