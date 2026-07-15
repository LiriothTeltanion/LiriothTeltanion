"""Synchronize verified NovaFit facts into the generated GitHub profile.

The remote project manifest is treated as untrusted input: only a small,
validated set of plain-text facts can update the existing NovaFit project.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

if __package__:
    from scripts import build_profile
else:
    import build_profile

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = ROOT / "profile.json"
DEFAULT_SNAPSHOT = ROOT / "data" / "project-snapshots" / "novafit.json"
DEFAULT_COMPACT_OUTPUT = ROOT / "README.md"
DEFAULT_EXPANDED_OUTPUT = ROOT / "README_EXPANDED.md"
DEFAULT_MANIFEST_URL = (
    "https://raw.githubusercontent.com/"
    "LiriothTeltanion/NovaFit/main/portfolio/project.json"
)
EXPECTED_REPOSITORY = "https://github.com/LiriothTeltanion/NovaFit"
EXPECTED_SCHEMA = "nova-portfolio-project-v1"
MAX_MANIFEST_BYTES = 512 * 1024
VERSION_PATTERN = re.compile(r"^[0-9]+(?:\.[0-9]+){2}(?:[-+][0-9A-Za-z.-]+)?$")


def build_parser() -> argparse.ArgumentParser:
    """Create the synchronization command-line interface."""
    parser = argparse.ArgumentParser(
        description="Sync NovaFit's public manifest into this generated profile."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--url",
        default=None,
        help="Fetch the manifest from NovaFit's allow-listed raw GitHub URL.",
    )
    source.add_argument("--manifest", type=Path, help="Read a local manifest file.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--write", action="store_true", help="Update the snapshot and profile."
    )
    mode.add_argument(
        "--check", action="store_true", help="Fail when generated files drift."
    )
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--compact-output", type=Path, default=DEFAULT_COMPACT_OUTPUT)
    parser.add_argument("--expanded-output", type=Path, default=DEFAULT_EXPANDED_OUTPUT)
    return parser


def load_manifest(path: Path) -> dict[str, Any]:
    """Load a size-limited local manifest and validate its complete contract."""
    payload = path.read_bytes()
    if len(payload) > MAX_MANIFEST_BYTES:
        raise ValueError(f"Manifest exceeds {MAX_MANIFEST_BYTES} bytes.")
    return validate_manifest(_decode_object(payload, str(path)))


def fetch_manifest(url: str, timeout: float = 15.0) -> dict[str, Any]:
    """Fetch the one allow-listed raw manifest with bounded network reads."""
    if url != DEFAULT_MANIFEST_URL:
        raise ValueError("Only NovaFit's canonical raw GitHub manifest URL is allowed.")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise ValueError("Manifest URL must use HTTPS on raw.githubusercontent.com.")
    request = Request(url, headers={"User-Agent": "Lirioth-profile-sync/1"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - exact URL allow-list
        advertised = response.headers.get("Content-Length")
        if advertised is not None and int(advertised) > MAX_MANIFEST_BYTES:
            raise ValueError(f"Manifest exceeds {MAX_MANIFEST_BYTES} bytes.")
        payload = response.read(MAX_MANIFEST_BYTES + 1)
    if len(payload) > MAX_MANIFEST_BYTES:
        raise ValueError(f"Manifest exceeds {MAX_MANIFEST_BYTES} bytes.")
    return validate_manifest(_decode_object(payload, url))


def _decode_object(payload: bytes, source: str) -> dict[str, Any]:
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Manifest is not valid UTF-8 JSON: {source}") from error
    if not isinstance(data, dict):
        raise ValueError("Manifest root must be an object.")
    return data


def validate_manifest(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Validate identity, types, bounds and plain-text fields before rendering."""
    _expect(raw.get("schema") == EXPECTED_SCHEMA, "Unexpected manifest schema.")
    _expect(raw.get("slug") == "novafit", "Unexpected project slug.")
    _expect(raw.get("name") == "NovaFit", "Unexpected project name.")
    _expect(raw.get("status") == "active", "NovaFit manifest is not active.")
    _expect(raw.get("default_branch") == "main", "NovaFit default branch must be main.")
    _expect(raw.get("repository") == EXPECTED_REPOSITORY, "Unexpected repository URL.")

    version = _plain_text(raw.get("version"), "version", 40)
    _expect(bool(VERSION_PATTERN.fullmatch(version)), "Version is not semantic.")
    _plain_text(raw.get("summary"), "summary", 600)

    languages = _plain_text_list(raw.get("languages"), "languages", 10, 12)
    _expect(set(languages) == {"en", "es", "he"}, "Languages must be en, es and he.")
    _bounded_int(raw.get("theme_count"), "theme_count", minimum=1, maximum=100)

    quality = _mapping(raw.get("quality"), "quality")
    _bounded_int(
        quality.get("automated_tests_discovered"),
        "quality.automated_tests_discovered",
        minimum=1,
        maximum=100_000,
    )
    _plain_text(
        quality.get("verification_command"), "quality.verification_command", 120
    )
    _plain_text(quality.get("release_audit"), "quality.release_audit", 240)

    capabilities = _plain_text_list(raw.get("capabilities"), "capabilities", 12, 180)
    _expect(
        len(capabilities) >= 3, "Manifest must publish at least three capabilities."
    )

    privacy = _mapping(raw.get("privacy"), "privacy")
    for field in (
        "local_first",
        "tracked_runtime_data",
        "weather_sends_health_records",
    ):
        _expect(
            isinstance(privacy.get(field), bool), f"privacy.{field} must be boolean."
        )
    _expect(privacy["local_first"] is True, "NovaFit must remain local-first.")
    _expect(
        privacy["tracked_runtime_data"] is False, "Runtime data must not be tracked."
    )
    _expect(
        privacy["weather_sends_health_records"] is False,
        "Weather integration must not send health records.",
    )

    assets = _mapping(raw.get("assets"), "assets")
    _bounded_int(assets.get("count"), "assets.count", minimum=1, maximum=10_000)
    _bounded_int(
        assets.get("total_bytes"), "assets.total_bytes", minimum=1, maximum=2**31
    )
    return dict(raw)


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be an object.")
    return value


def _plain_text(value: Any, path: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(
            f"{path} must be non-empty plain text up to {maximum} characters."
        )
    if value != value.strip() or any(character in value for character in "\r\n<>[]|"):
        raise ValueError(f"{path} contains unsafe Markdown or control characters.")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{path} contains control characters.")
    return value


def _plain_text_list(
    value: Any, path: str, maximum_items: int, maximum_text: int
) -> list[str]:
    if not isinstance(value, list) or not value or len(value) > maximum_items:
        raise ValueError(
            f"{path} must be a non-empty array of at most {maximum_items} items."
        )
    result = [
        _plain_text(item, f"{path}[{index}]", maximum_text)
        for index, item in enumerate(value)
    ]
    if len({item.casefold() for item in result}) != len(result):
        raise ValueError(f"{path} contains duplicate values.")
    return result


def _bounded_int(value: Any, path: str, *, minimum: int, maximum: int) -> int:
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


def apply_manifest(
    profile: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    """Return a copied profile with only the allow-listed NovaFit fields updated."""
    validated = validate_manifest(manifest)
    updated = copy.deepcopy(dict(profile))
    projects = updated.get("projects")
    if not isinstance(projects, list):
        raise ValueError("profile.projects must be an array.")
    matches = [
        project
        for project in projects
        if isinstance(project, dict)
        and project.get("name") == "NovaFit"
        and project.get("source") == EXPECTED_REPOSITORY
    ]
    if len(matches) != 1:
        raise ValueError("Profile must contain exactly one canonical NovaFit project.")

    project = matches[0]
    quality = validated["quality"]
    assets = validated["assets"]
    version = validated["version"]
    test_count = quality["automated_tests_discovered"]
    theme_count = validated["theme_count"]
    project["status"] = f"Active v{version} local-first desktop product"
    project["solution"] = validated["summary"]
    project["evidence"] = (
        f"{test_count} discovered automated tests, {theme_count} themes, EN/ES/HE RTL UX, "
        f"verified complete backups, {assets['count']} public visual assets, one-click "
        "verification and strict release audit"
    )
    project["highlights"] = [
        capability[0].upper() + capability[1:]
        for capability in validated["capabilities"]
    ]
    project["portfolio_sync"] = {
        "schema": EXPECTED_SCHEMA,
        "source": DEFAULT_MANIFEST_URL,
        "version": version,
        "theme_count": theme_count,
        "automated_tests_discovered": test_count,
        "verification_command": quality["verification_command"],
        "release_audit": quality["release_audit"],
        "asset_count": assets["count"],
    }
    build_profile._validate_profile_data(updated)
    return updated


def render_outputs(profile: Mapping[str, Any]) -> tuple[str, str]:
    """Render both public README modes from one synchronized profile object."""
    return (
        build_profile.render_profile(profile, "compact"),
        build_profile.render_profile(profile, "expanded"),
    )


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def _write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)
    return True


def _load_source(args: argparse.Namespace) -> dict[str, Any]:
    if args.url is not None:
        return fetch_manifest(args.url)
    return load_manifest(args.manifest or args.snapshot)


def synchronize(args: argparse.Namespace) -> list[Path]:
    """Calculate expected outputs and either write them or return drift paths."""
    manifest = _load_source(args)
    profile = json.loads(args.profile.read_text(encoding="utf-8"))
    if not isinstance(profile, dict):
        raise ValueError("Profile JSON root must be an object.")
    expected_profile = apply_manifest(profile, manifest)
    compact, expanded = render_outputs(expected_profile)
    expected = {
        args.snapshot: _canonical_json(manifest),
        args.profile: _canonical_json(expected_profile),
        args.compact_output: compact,
        args.expanded_output: expanded,
    }
    changed: list[Path] = []
    for path, content in expected.items():
        if args.write:
            if _write_if_changed(path, content):
                changed.append(path)
        elif not path.exists() or path.read_text(encoding="utf-8") != content:
            changed.append(path)
    return changed


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        changed = synchronize(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"NovaFit profile sync failed: {error}", file=sys.stderr)
        return 2
    if args.write:
        if changed:
            for path in changed:
                try:
                    display = path.resolve().relative_to(ROOT)
                except ValueError:
                    display = path
                print(f"updated {display}")
        else:
            print("[OK] NovaFit profile facts are already current.")
        return 0
    if changed:
        print("NovaFit profile facts are out of date:", file=sys.stderr)
        for path in changed:
            print(f"  - {path}", file=sys.stderr)
        print(
            f"Run: python scripts/sync_novafit.py --url {DEFAULT_MANIFEST_URL} --write",
            file=sys.stderr,
        )
        return 1
    print("[OK] NovaFit profile facts and generated READMEs are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
