"""Integration coverage for the profile release/tag integrity gate."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class ReleaseIntegrityVerifierTests(unittest.TestCase):
    """Exercise candidate and released states in isolated Git repositories."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.powershell = shutil.which("powershell") or shutil.which("pwsh")
        if cls.powershell is None:
            raise unittest.SkipTest("PowerShell is required for release-integrity tests.")
        profile = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
        cls.profile_version = profile["profile_version"]
        cls.release_tag = f"v{cls.profile_version}"

    def git(self, repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def create_repository(self, parent: Path, status: str) -> Path:
        repository = parent / "profile"
        verifier_directory = repository / "tools" / "profile"
        verifier_directory.mkdir(parents=True)
        shutil.copy2(ROOT / "profile.json", repository / "profile.json")
        shutil.copy2(
            ROOT / "tools" / "profile" / "verify-profile.ps1",
            verifier_directory / "verify-profile.ps1",
        )
        (repository / "release-notes.txt").write_text(
            "Release-integrity fixture.\n", encoding="utf-8", newline="\n"
        )
        self.set_release_status(repository, status)
        self.git(repository, "init", "-b", "main")
        self.git(repository, "config", "user.name", "Release Integrity Test")
        self.git(repository, "config", "user.email", "release-integrity@example.invalid")
        self.git(repository, "add", "--all")
        self.git(repository, "commit", "-m", f"test: prepare {status} profile")
        return repository

    def set_release_status(self, repository: Path, status: str) -> None:
        profile_path = repository / "profile.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile["release"]["status"] = status
        profile_path.write_text(
            json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def tag(self, repository: Path, *, annotated: bool) -> None:
        if annotated:
            self.git(
                repository,
                "tag",
                "-a",
                self.release_tag,
                "-m",
                f"Profile {self.profile_version}",
            )
        else:
            self.git(repository, "tag", self.release_tag)

    def verify(self, repository: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                self.powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(repository / "tools" / "profile" / "verify-profile.ps1"),
                "-RepositoryPath",
                str(repository),
                "-ReleaseOnly",
            ],
            cwd=repository,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_candidate_without_tag_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "release-candidate")
            result = self.verify(repository)

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(f"local tag '{self.release_tag}' is available", result.stdout)

    def test_candidate_cannot_reuse_existing_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "release-candidate")
            self.tag(repository, annotated=True)
            result = self.verify(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            f"cannot reuse the existing local tag '{self.release_tag}'", result.stdout
        )

    def test_released_profile_requires_a_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "released")
            result = self.verify(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            f"requires the matching annotated local tag '{self.release_tag}'",
            result.stdout,
        )

    def test_released_profile_rejects_lightweight_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "released")
            self.tag(repository, annotated=False)
            result = self.verify(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lightweight tags are not accepted", result.stdout)

    def test_released_profile_rejects_tag_on_candidate_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "release-candidate")
            self.tag(repository, annotated=True)
            self.set_release_status(repository, "released")
            self.git(repository, "add", "profile.json")
            self.git(repository, "commit", "-m", "test: finalize after tag")
            result = self.verify(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("but the checked-out commit is", result.stdout)

    def test_released_profile_requires_clean_tracked_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "released")
            self.tag(repository, annotated=True)
            release_notes = repository / "release-notes.txt"
            release_notes.write_text(
                release_notes.read_text(encoding="utf-8")
                + "Uncommitted test change.\n",
                encoding="utf-8",
                newline="\n",
            )
            result = self.verify(repository)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires a clean tracked worktree and index", result.stdout)

    def test_released_profile_accepts_exact_annotated_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "released")
            self.tag(repository, annotated=True)
            result = self.verify(repository)

        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(
            f"Release integrity confirmed: annotated {self.release_tag}", result.stdout
        )


if __name__ == "__main__":
    unittest.main()
