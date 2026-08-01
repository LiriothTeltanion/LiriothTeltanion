"""Audit and stage verified Nova Music Lab release media for the public profile.

The default mode is deliberately read-only. A write never updates public profile
files: it creates an ignored local candidate package that still requires visual
review, a profile version decision and explicit publication approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
from datetime import date
from pathlib import Path, PurePosixPath
from time import time_ns
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SNAPSHOT = ROOT / "data" / "project-snapshots" / "nova-music-lab.json"
DEFAULT_CANDIDATE_ROOT = ROOT / ".cache" / "nova-music-lab-profile-candidates"
DEFAULT_PROFILE = ROOT / "profile.json"
DEFAULT_MANIFEST_URL = (
    "https://liriothteltanion.github.io/NovaMusicLab/"
    "release-profile-manifest.json"
)
EXPECTED_SCHEMA = "nova-music-profile-release-v1"
EXPECTED_REPOSITORY_SLUG = "LiriothTeltanion/NovaMusicLab"
EXPECTED_REPOSITORY_URL = "https://github.com/LiriothTeltanion/NovaMusicLab"
EXPECTED_LIVE_URL = "https://liriothteltanion.github.io/NovaMusicLab/"
EXPECTED_BRANCH = "main"
REQUIRED_MEDIA_IDS = {
    "profile-hero-desktop",
    "profile-hero-mobile",
    "profile-tour",
    "profile-tour-static",
    "social-preview",
}
STATIC_MEDIA_IDS = {
    "profile-hero-desktop",
    "profile-hero-mobile",
    "profile-tour-static",
    "social-preview",
}
MAX_MANIFEST_BYTES = 256 * 1024
MAX_MEDIA_BYTES = 5 * 1024 * 1024
MAX_TOTAL_MEDIA_BYTES = 8 * 1024 * 1024
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA1_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MEDIA_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png"}


def build_parser() -> argparse.ArgumentParser:
    """Create the safe synchronization command-line interface."""
    parser = argparse.ArgumentParser(
        description=(
            "Audit Nova Music Lab's deployed release manifest or stage an ignored "
            "local profile candidate."
        )
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--url",
        default=None,
        help="Fetch the exact allow-listed Nova Music Lab release manifest.",
    )
    source.add_argument(
        "--manifest",
        type=Path,
        help="Read a local manifest and its media from a Nova Music Lab Git checkout.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Read-only drift check (the default).",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Stage an ignored local candidate; never changes public profile files.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="Nova Music Lab Git root for --manifest; inferred when omitted.",
    )
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    parser.add_argument(
        "--profile-root",
        type=Path,
        default=ROOT,
        help=argparse.SUPPRESS,
    )
    return parser


def validate_manifest(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the complete release and media contract as untrusted input."""
    _expect(raw.get("schema") == EXPECTED_SCHEMA, "Unexpected manifest schema.")
    _expect(
        raw.get("repository") == EXPECTED_REPOSITORY_SLUG,
        "Unexpected repository identity.",
    )
    _expect(
        raw.get("default_branch") == EXPECTED_BRANCH,
        "Nova Music Lab default branch must be main.",
    )
    _expect(raw.get("live_url") == EXPECTED_LIVE_URL, "Unexpected live URL.")

    release = _mapping(raw.get("release"), "release")
    status = _plain_text(release.get("status"), "release.status", 40)
    _expect(
        status in {"private-candidate", "deployed"},
        "release.status must be private-candidate or deployed.",
    )
    version = _plain_text(release.get("version"), "release.version", 40)
    _expect(bool(VERSION_PATTERN.fullmatch(version)), "Release version is not semantic.")
    commit = release.get("commit")
    if commit is not None:
        commit = _plain_text(commit, "release.commit", 40)
        _expect(bool(SHA1_PATTERN.fullmatch(commit)), "Release commit must be a full SHA-1.")
    captured_on = _nullable_iso_date(release.get("captured_on"), "release.captured_on")
    deployed_on = _nullable_iso_date(release.get("deployed_on"), "release.deployed_on")
    if status == "deployed":
        _expect(commit is not None, "A deployed release requires a full commit SHA-1.")
        _expect(deployed_on is not None, "A deployed release requires deployed_on.")
    else:
        _expect(deployed_on is None, "A private candidate cannot claim deployed_on.")
    if captured_on is not None and deployed_on is not None:
        _expect(
            captured_on <= deployed_on,
            "release.captured_on cannot be later than release.deployed_on.",
        )

    raw_media = raw.get("media")
    if not isinstance(raw_media, list) or not raw_media or len(raw_media) > 24:
        raise ValueError("media must be a non-empty array of at most 24 items.")
    media: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    total_bytes = 0
    expected_prefix = f"assets/releases/v{version}/"
    for index, value in enumerate(raw_media):
        item = _mapping(value, f"media[{index}]")
        media_id = _plain_text(item.get("id"), f"media[{index}].id", 80)
        _expect(
            re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", media_id) is not None,
            f"media[{index}].id must use lowercase kebab-case.",
        )
        path = _safe_source_path(item.get("path"), f"media[{index}].path")
        _expect(
            path.startswith(expected_prefix),
            f"media[{index}].path must stay under {expected_prefix}.",
        )
        suffix = PurePosixPath(path).suffix.lower()
        _expect(suffix in MEDIA_EXTENSIONS, f"media[{index}].path has an unsafe type.")
        if media_id == "profile-tour":
            _expect(suffix == ".gif", "profile-tour must be a GIF.")
        if media_id == "social-preview":
            _expect(suffix == ".png", "social-preview must be a PNG.")
        if media_id in STATIC_MEDIA_IDS:
            _expect(suffix != ".gif", f"{media_id} must be a static image.")
        _expect(media_id not in seen_ids, f"Duplicate media id: {media_id}.")
        _expect(path not in seen_paths, f"Duplicate media path: {path}.")
        seen_ids.add(media_id)
        seen_paths.add(path)

        sha256 = _plain_text(item.get("sha256"), f"media[{index}].sha256", 64)
        _expect(
            bool(SHA256_PATTERN.fullmatch(sha256)),
            f"media[{index}].sha256 must be lowercase SHA-256.",
        )
        width = _bounded_int(item.get("width"), f"media[{index}].width", 1, 16_384)
        height = _bounded_int(item.get("height"), f"media[{index}].height", 1, 16_384)
        if media_id == "social-preview":
            _expect(
                (width, height) == (1280, 640),
                "social-preview must be exactly 1280 by 640 pixels.",
            )
        size = _bounded_int(
            item.get("bytes"),
            f"media[{index}].bytes",
            1,
            MAX_MEDIA_BYTES,
        )
        total_bytes += size
        language = _plain_text(item.get("lang"), f"media[{index}].lang", 32)
        _expect(
            language in {"en", "es", "he", "multilingual"},
            f"media[{index}].lang is unsupported.",
        )
        theme = _plain_text(item.get("theme"), f"media[{index}].theme", 80)
        viewport_value = _mapping(item.get("viewport"), f"media[{index}].viewport")
        _expect(
            set(viewport_value) == {"width", "height"},
            f"media[{index}].viewport must contain only width and height.",
        )
        viewport = {
            "width": _bounded_int(
                viewport_value.get("width"),
                f"media[{index}].viewport.width",
                1,
                16_384,
            ),
            "height": _bounded_int(
                viewport_value.get("height"),
                f"media[{index}].viewport.height",
                1,
                16_384,
            ),
        }
        media.append(
            {
                "id": media_id,
                "path": path,
                "sha256": sha256,
                "width": width,
                "height": height,
                "bytes": size,
                "lang": language,
                "theme": theme,
                "viewport": viewport,
            }
        )
    missing = sorted(REQUIRED_MEDIA_IDS - seen_ids)
    _expect(not missing, f"Missing required profile media: {', '.join(missing)}.")
    _expect(
        total_bytes <= MAX_TOTAL_MEDIA_BYTES,
        f"Profile media exceeds the {MAX_TOTAL_MEDIA_BYTES}-byte total budget.",
    )
    return {
        "schema": EXPECTED_SCHEMA,
        "repository": EXPECTED_REPOSITORY_SLUG,
        "default_branch": EXPECTED_BRANCH,
        "live_url": EXPECTED_LIVE_URL,
        "release": {
            "status": status,
            "version": version,
            "commit": commit,
            "captured_on": captured_on,
            "deployed_on": deployed_on,
        },
        "media": media,
    }


def load_manifest(path: Path) -> dict[str, Any]:
    """Load a bounded local UTF-8 JSON manifest."""
    payload = path.read_bytes()
    if len(payload) > MAX_MANIFEST_BYTES:
        raise ValueError(f"Manifest exceeds {MAX_MANIFEST_BYTES} bytes.")
    return validate_manifest(_decode_object(payload, str(path)))


def fetch_manifest(url: str, timeout: float = 15.0) -> dict[str, Any]:
    """Fetch only the cache-bypassed manifest served by the deployed app."""
    if url != DEFAULT_MANIFEST_URL:
        raise ValueError(
            "Only Nova Music Lab's canonical live deployed manifest URL is allowed."
        )
    manifest = validate_manifest(
        _decode_object(_fetch_live_manifest_bytes(url, MAX_MANIFEST_BYTES, timeout), url)
    )
    _expect(
        manifest["release"]["status"] == "deployed",
        "The canonical live manifest must describe a deployed release, not a "
        "tracked private candidate.",
    )
    return manifest


def load_verified_bundle(
    *,
    manifest_path: Path | None,
    manifest_url: str | None,
    source_root: Path | None,
) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Load one manifest and verify version, commit, hashes and image dimensions."""
    if manifest_path is not None:
        manifest = load_manifest(manifest_path)
        project_root = source_root or _git_root(manifest_path.parent)
        blobs = _load_local_commit_bundle(project_root, manifest)
    else:
        url = manifest_url or DEFAULT_MANIFEST_URL
        manifest = fetch_manifest(url)
        blobs = _load_remote_commit_bundle(manifest)
    verify_media(manifest, blobs)
    return manifest, blobs


def verify_media(manifest: Mapping[str, Any], blobs: Mapping[str, bytes]) -> None:
    """Verify every declared byte count, digest and raster dimension."""
    expected_media = manifest["media"]
    expected_paths = {item["path"] for item in expected_media}
    _expect(set(blobs) == expected_paths, "Verified media paths do not match manifest.")
    for item in expected_media:
        payload = blobs[item["path"]]
        _expect(len(payload) == item["bytes"], f"{item['id']} byte count does not match.")
        digest = hashlib.sha256(payload).hexdigest()
        _expect(digest == item["sha256"], f"{item['id']} SHA-256 does not match.")
        width, height = _image_dimensions(payload, PurePosixPath(item["path"]).suffix)
        _expect(
            (width, height) == (item["width"], item["height"]),
            f"{item['id']} dimensions do not match.",
        )


def audit_reviewed_state(
    manifest: Mapping[str, Any],
    blobs: Mapping[str, bytes],
    *,
    snapshot_path: Path,
    profile_path: Path,
    profile_root: Path,
) -> list[str]:
    """Return read-only drift findings for the reviewed profile state."""
    findings: list[str] = []
    release = manifest["release"]
    if release["status"] != "deployed":
        findings.append("upstream release is private-candidate, not deployed")
        return findings
    if not snapshot_path.exists():
        findings.append(f"reviewed snapshot is missing: {snapshot_path}")
        return findings
    reviewed = load_manifest(snapshot_path)
    if _canonical_json(reviewed) != _canonical_json(manifest):
        findings.append("reviewed snapshot differs from the deployed source manifest")
        return findings

    targets = profile_targets(manifest)
    by_id = {item["id"]: item for item in manifest["media"]}
    for media_id, target_path in targets.items():
        item = by_id[media_id]
        target = profile_root / target_path
        if not target.exists():
            findings.append(f"profile media is missing: {target_path}")
            continue
        if target.read_bytes() != blobs[item["path"]]:
            findings.append(f"profile media is stale: {target_path}")

    readme_media_ids = REQUIRED_MEDIA_IDS - {"social-preview"}
    for readme_name in ("README.md", "README_EXPANDED.md"):
        readme_path = profile_root / readme_name
        if not readme_path.exists():
            findings.append(f"generated profile is missing: {readme_name}")
            continue
        content = readme_path.read_text(encoding="utf-8")
        for media_id in sorted(readme_media_ids):
            target_path = targets[media_id]
            if f"./{target_path}" not in content:
                findings.append(
                    f"{readme_name} does not reference current {media_id}: "
                    f"{target_path}"
                )

    if not profile_path.exists():
        findings.append(f"profile data is missing: {profile_path}")
        return findings
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        findings.append(f"profile data cannot be read: {error}")
        return findings
    if not isinstance(profile, Mapping):
        findings.append("profile data root is not an object")
        return findings
    projects = profile.get("projects")
    matches = (
        [
            project
            for project in projects
            if isinstance(project, Mapping)
            and project.get("name") == "Nova Music Lab"
            and project.get("source") == EXPECTED_REPOSITORY_URL
        ]
        if isinstance(projects, list)
        else []
    )
    if len(matches) != 1:
        findings.append("profile must contain one canonical Nova Music Lab project")
        return findings
    sync = matches[0].get("portfolio_sync")
    if sync != expected_profile_sync(manifest):
        findings.append("Nova Music Lab portfolio_sync does not match deployed evidence")
    return findings


def stage_candidate(
    manifest: Mapping[str, Any],
    blobs: Mapping[str, bytes],
    *,
    candidate_root: Path,
    branch: str,
) -> tuple[Path, list[Path]]:
    """Create one additive local candidate package after enforcing safety gates."""
    release = manifest["release"]
    _expect(release["status"] == "deployed", "--write accepts only deployed releases.")
    _expect(
        isinstance(release["commit"], str)
        and SHA1_PATTERN.fullmatch(release["commit"]) is not None,
        "--write requires a full release commit SHA-1.",
    )
    _expect(release["deployed_on"] is not None, "--write requires deployed_on.")
    normalized_branch = branch.strip()
    _expect(normalized_branch != "", "--write requires a named profile branch.")
    _expect(
        normalized_branch not in {"main", "master", "trunk"},
        "--write is forbidden on the profile's protected default branch.",
    )
    verify_media(manifest, blobs)

    candidate_dir = (
        candidate_root
        / f"v{release['version']}-{release['commit'][:12]}"
    )
    targets = profile_targets(manifest)
    plan = {
        "schema": "nova-music-profile-candidate-v1",
        "source_manifest": "release-profile-manifest.json",
        "profile_version_unchanged": True,
        "publication_authorized": False,
        "review_required": [
            "desktop visual QA",
            "mobile visual QA",
            "GIF and reduced-motion review",
            "public-data and privacy review",
            "profile Semantic Versioning decision",
        ],
        "portfolio_sync": expected_profile_sync(manifest),
        "media": [
            {
                "id": item["id"],
                "candidate": f"media/{item['id']}{PurePosixPath(item['path']).suffix.lower()}",
                "profile_target": targets.get(item["id"]),
                "sha256": item["sha256"],
            }
            for item in manifest["media"]
        ],
    }
    expected_files: dict[Path, bytes] = {
        candidate_dir / "release-profile-manifest.json": _canonical_json(manifest).encode(
            "utf-8"
        ),
        candidate_dir / "candidate-plan.json": _canonical_json(plan).encode("utf-8"),
    }
    for item in manifest["media"]:
        suffix = PurePosixPath(item["path"]).suffix.lower()
        expected_files[candidate_dir / "media" / f"{item['id']}{suffix}"] = blobs[
            item["path"]
        ]

    changed: list[Path] = []
    for path, payload in expected_files.items():
        if path.exists():
            _expect(
                path.read_bytes() == payload,
                f"Candidate path already exists with different content: {path}.",
            )
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(payload)
        temporary.replace(path)
        changed.append(path)
    return candidate_dir, changed


def profile_targets(manifest: Mapping[str, Any]) -> dict[str, str]:
    """Map canonical media IDs to deliberate profile-owned target paths."""
    by_id = {item["id"]: item for item in manifest["media"]}
    desktop_suffix = PurePosixPath(by_id["profile-hero-desktop"]["path"]).suffix.lower()
    mobile_suffix = PurePosixPath(by_id["profile-hero-mobile"]["path"]).suffix.lower()
    tour_static_suffix = PurePosixPath(
        by_id["profile-tour-static"]["path"]
    ).suffix.lower()
    social_suffix = PurePosixPath(by_id["social-preview"]["path"]).suffix.lower()
    return {
        "profile-hero-desktop": f"assets/nova-music-live-preview{desktop_suffix}",
        "profile-hero-mobile": (
            f"assets/nova-music-live-preview-mobile{mobile_suffix}"
        ),
        "profile-tour": "assets/nova-music-product-tour.gif",
        "profile-tour-static": (
            f"assets/nova-music-product-tour-static{tour_static_suffix}"
        ),
        "social-preview": f"assets/social/novamusiclab-social-preview{social_suffix}",
    }


def expected_profile_sync(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact evidence record required during a reviewed promotion."""
    release = manifest["release"]
    return {
        "schema": EXPECTED_SCHEMA,
        "source": DEFAULT_MANIFEST_URL,
        "version": release["version"],
        "status": release["status"],
        "commit": release["commit"],
        "captured_on": release["captured_on"],
        "deployed_on": release["deployed_on"],
        "media": profile_targets(manifest),
    }


def _load_remote_commit_bundle(manifest: Mapping[str, Any]) -> dict[str, bytes]:
    release = manifest["release"]
    commit = release["commit"]
    if commit is None:
        _expect(
            release["status"] == "private-candidate",
            "Only a private candidate may omit its release commit.",
        )
        revision = EXPECTED_BRANCH
    else:
        _expect(
            isinstance(commit, str) and SHA1_PATTERN.fullmatch(commit) is not None,
            "Remote verification requires a full release commit SHA-1.",
        )
        revision = commit
    raw_base = (
        "https://raw.githubusercontent.com/LiriothTeltanion/NovaMusicLab/"
        f"{revision}/"
    )
    package = _decode_object(
        _fetch_bytes(f"{raw_base}package.json", 128 * 1024, 15.0),
        f"{raw_base}package.json",
    )
    _expect(
        package.get("version") == release["version"],
        "package.json version does not match the release manifest.",
    )
    return {
        item["path"]: _fetch_bytes(
            f"{raw_base}{item['path']}",
            min(MAX_MEDIA_BYTES, item["bytes"]) + 1,
            30.0,
        )
        for item in manifest["media"]
    }


def _load_local_commit_bundle(
    source_root: Path, manifest: Mapping[str, Any]
) -> dict[str, bytes]:
    _validate_local_repository_identity(source_root)
    release = manifest["release"]
    commit = release["commit"]
    if commit is None:
        _expect(
            release["status"] == "private-candidate",
            "Only a private candidate may omit its release commit.",
        )
        package_path = source_root / "package.json"
        package = _decode_object(
            package_path.read_bytes(),
            str(package_path),
        )
        _expect(
            package.get("version") == release["version"],
            "package.json version does not match the release manifest.",
        )
        blobs: dict[str, bytes] = {}
        for item in manifest["media"]:
            media_path = source_root.joinpath(*PurePosixPath(item["path"]).parts)
            payload = media_path.read_bytes()
            _expect(
                len(payload) <= MAX_MEDIA_BYTES,
                f"Release media exceeds {MAX_MEDIA_BYTES} bytes: {item['path']}.",
            )
            blobs[item["path"]] = payload
        return blobs
    _expect(
        isinstance(commit, str) and SHA1_PATTERN.fullmatch(commit) is not None,
        "Local verification requires a full release commit SHA-1.",
    )
    package = _decode_object(
        _git_show(source_root, commit, "package.json"),
        f"{commit}:package.json",
    )
    _expect(
        package.get("version") == release["version"],
        "package.json version does not match the release manifest.",
    )
    return {
        item["path"]: _git_show(source_root, commit, item["path"])
        for item in manifest["media"]
    }


def _git_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise ValueError("Could not infer the Nova Music Lab Git root.")
    return Path(result.stdout.strip())


def _validate_local_repository_identity(root: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(root), "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise ValueError("Local source must have the canonical Nova Music Lab origin.")
    origin = result.stdout.strip().removesuffix(".git")
    _expect(
        origin == EXPECTED_REPOSITORY_URL,
        "Local source origin is not the canonical Nova Music Lab repository.",
    )


def _git_show(root: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{path}"],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ValueError(f"Release commit does not contain {path}.")
    if len(result.stdout) > MAX_MEDIA_BYTES and path != "package.json":
        raise ValueError(f"Release media exceeds {MAX_MEDIA_BYTES} bytes: {path}.")
    return result.stdout


def _current_branch(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "branch", "--show-current"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise ValueError("Could not determine the current profile branch.")
    return result.stdout.strip()


def _validate_candidate_root(path: Path) -> None:
    allowed_root = (ROOT / ".cache").resolve()
    candidate_root = path.resolve()
    _expect(
        candidate_root == allowed_root or candidate_root.is_relative_to(allowed_root),
        "--candidate-root must stay inside the profile's ignored .cache directory.",
    )


def _fetch_bytes(url: str, limit: int, timeout: float) -> bytes:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise ValueError("Release evidence must use HTTPS on raw.githubusercontent.com.")
    request = Request(url, headers={"User-Agent": "Lirioth-profile-sync/1"})
    return _read_bounded_response(request, limit, timeout)


def _fetch_live_manifest_bytes(url: str, limit: int, timeout: float) -> bytes:
    """Fetch deployed attestation with an explicit cache bypass."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "liriothteltanion.github.io"
        or parsed.path != "/NovaMusicLab/release-profile-manifest.json"
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("The release manifest must use the canonical GitHub Pages URL.")
    request_url = f"{url}?profile-sync={time_ns()}"
    request = Request(
        request_url,
        headers={
            "User-Agent": "Lirioth-profile-sync/1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    return _read_bounded_response(request, limit, timeout)


def _read_bounded_response(request: Request, limit: int, timeout: float) -> bytes:
    """Read one HTTP response without trusting its advertised size."""
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - exact origin
        advertised = response.headers.get("Content-Length")
        if advertised is not None and int(advertised) > limit:
            raise ValueError(f"Remote file exceeds {limit} bytes: {request.full_url}.")
        payload = response.read(limit + 1)
    if len(payload) > limit:
        raise ValueError(f"Remote file exceeds {limit} bytes: {request.full_url}.")
    return payload


def _image_dimensions(payload: bytes, suffix: str) -> tuple[int, int]:
    suffix = suffix.lower()
    if suffix == ".png":
        if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("PNG media has an invalid signature.")
        return struct.unpack(">II", payload[16:24])
    if suffix == ".gif":
        if len(payload) < 10 or payload[:6] not in {b"GIF87a", b"GIF89a"}:
            raise ValueError("GIF media has an invalid signature.")
        return struct.unpack("<HH", payload[6:10])
    if suffix in {".jpg", ".jpeg"}:
        return _jpeg_dimensions(payload)
    raise ValueError(f"Unsupported image extension: {suffix}.")


def _jpeg_dimensions(payload: bytes) -> tuple[int, int]:
    if len(payload) < 4 or payload[:2] != b"\xff\xd8":
        raise ValueError("JPEG media has an invalid signature.")
    position = 2
    start_of_frame = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while position + 3 < len(payload):
        if payload[position] != 0xFF:
            position += 1
            continue
        while position < len(payload) and payload[position] == 0xFF:
            position += 1
        if position >= len(payload):
            break
        marker = payload[position]
        position += 1
        if marker in {0x01, 0xD8, 0xD9}:
            continue
        if position + 2 > len(payload):
            break
        segment_length = int.from_bytes(payload[position : position + 2], "big")
        if segment_length < 2 or position + segment_length > len(payload):
            break
        if marker in start_of_frame:
            if segment_length < 7:
                break
            height = int.from_bytes(payload[position + 3 : position + 5], "big")
            width = int.from_bytes(payload[position + 5 : position + 7], "big")
            return width, height
        position += segment_length
    raise ValueError("JPEG media does not contain a valid size marker.")


def _decode_object(payload: bytes, source: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid UTF-8 JSON: {source}.") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {source}.")
    return value


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object.")
    return value


def _plain_text(value: Any, path: str, maximum: int) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise ValueError(f"{path} must be non-empty text up to {maximum} characters.")
    if value != value.strip() or any(character in value for character in "\r\n<>[]|"):
        raise ValueError(f"{path} contains unsafe text.")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{path} contains control characters.")
    return value


def _safe_source_path(value: Any, path: str) -> str:
    text = _plain_text(value, path, 240)
    _expect("\\" not in text, f"{path} must use forward slashes.")
    _expect(
        re.fullmatch(r"[A-Za-z0-9._/-]+", text) is not None,
        f"{path} contains unsupported characters.",
    )
    parsed = PurePosixPath(text)
    _expect(not parsed.is_absolute(), f"{path} must be relative.")
    _expect(
        all(part not in {"", ".", ".."} for part in parsed.parts),
        f"{path} contains an unsafe path segment.",
    )
    return parsed.as_posix()


def _nullable_iso_date(value: Any, path: str) -> str | None:
    if value is None:
        return None
    text = _plain_text(value, path, 10)
    _expect(bool(ISO_DATE_PATTERN.fullmatch(text)), f"{path} must use YYYY-MM-DD.")
    try:
        date.fromisoformat(text)
    except ValueError as error:
        raise ValueError(
            f"{path} must be a real calendar date in YYYY-MM-DD."
        ) from error
    return text


def _bounded_int(value: Any, path: str, minimum: int, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{path} must be an integer from {minimum} through {maximum}.")
    return value


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        _expect(
            not (args.write and args.manifest is not None),
            "--write accepts only the canonical public manifest URL.",
        )
        manifest, blobs = load_verified_bundle(
            manifest_path=args.manifest,
            manifest_url=args.url,
            source_root=args.source_root,
        )
        if args.write:
            _validate_candidate_root(args.candidate_root)
            branch = _current_branch(ROOT)
            candidate_dir, changed = stage_candidate(
                manifest,
                blobs,
                candidate_root=args.candidate_root,
                branch=branch,
            )
            if changed:
                print(f"[OK] Staged local candidate: {candidate_dir}")
                for path in changed:
                    print(f"  - {path}")
            else:
                print(f"[OK] Local candidate already matches: {candidate_dir}")
            print("Public profile files were not changed.")
            return 0

        findings = audit_reviewed_state(
            manifest,
            blobs,
            snapshot_path=args.snapshot,
            profile_path=args.profile,
            profile_root=args.profile_root,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Nova Music Lab profile audit failed: {error}", file=sys.stderr)
        return 2
    if findings:
        print("Nova Music Lab profile evidence needs review:", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        print(
            "After deployment, use --write on a non-main review branch to stage a "
            "local candidate.",
            file=sys.stderr,
        )
        return 1
    print("[OK] Nova Music Lab deployed evidence and profile media are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
