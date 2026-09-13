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

    def verify(
        self, repository: Path, *, allow_pending_tag: bool = False
    ) -> subprocess.CompletedProcess[str]:
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
                *(["-AllowPendingTag"] if allow_pending_tag else []),
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

    def test_pending_tag_is_tolerated_only_while_the_tag_is_absent(self) -> None:
        """A released commit under review has no tag yet, and never can.

        Branch protection makes the release commit reach the default branch only
        after review, and the tag can only be created once it is there. On a pull
        request the checked-out commit is a synthetic merge that no tag will ever
        name, so the tag rule is unevaluable rather than violated. The switch says
        so without lowering anything else, and it must not silence a tag that does
        exist and is wrong.
        """
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "released")
            tolerated = self.verify(repository, allow_pending_tag=True)
            self.assertEqual(
                tolerated.returncode, 0, msg=tolerated.stdout + tolerated.stderr
            )
            self.assertIn("the tag remains outstanding", tolerated.stdout)
            self.assertNotIn("Release integrity confirmed", tolerated.stdout)

            # Sin el interruptor, el mismo estado sigue siendo un fallo.
            strict = self.verify(repository)
            self.assertNotEqual(strict.returncode, 0)

            # Y con una etiqueta ligera presente, el interruptor no la perdona.
            self.tag(repository, annotated=False)
            lightweight = self.verify(repository, allow_pending_tag=True)

        self.assertNotEqual(lightweight.returncode, 0)
        self.assertIn("lightweight tags are not accepted", lightweight.stdout)

    def test_pending_tag_tolerates_a_tag_that_names_another_commit(self) -> None:
        """Every branch after a release sits ahead of its own tag.

        Once a version is tagged, any later commit that has not bumped the
        version still carries the released profile.json while HEAD has moved on.
        Off the default branch that mismatch is the normal state, not a defect,
        so it must not block ordinary work. The content check still runs: the
        working profile.json has to be byte-identical to the tagged one.
        """
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "released")
            self.tag(repository, annotated=True)
            (repository / "release-notes.txt").write_text(
                "Unrelated later work.\n", encoding="utf-8", newline="\n"
            )
            self.git(repository, "add", "--all")
            self.git(repository, "commit", "-m", "test: work after the tag")

            tolerated = self.verify(repository, allow_pending_tag=True)
            self.assertEqual(
                tolerated.returncode, 0, msg=tolerated.stdout + tolerated.stderr
            )
            self.assertIn("commit identity is verified on push", tolerated.stdout)
            self.assertNotIn("Release integrity confirmed", tolerated.stdout)

            # En main, ese mismo estado sigue siendo un fallo.
            strict = self.verify(repository)
            self.assertNotEqual(strict.returncode, 0)
            self.assertIn("but the checked-out commit is", strict.stdout)

    def test_pending_tag_does_not_excuse_edited_release_metadata(self) -> None:
        """Touching a released profile.json without bumping is still fatal."""
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "released")
            self.tag(repository, annotated=True)
            profile_path = repository / "profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["release"]["summary"] = "Edited after the tag was published."
            profile_path.write_text(
                json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            self.git(repository, "add", "--all")
            self.git(repository, "commit", "-m", "test: edit a published profile")
            result = self.verify(repository, allow_pending_tag=True)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not byte-equivalent", result.stdout)

    def test_pending_tag_still_requires_a_clean_tracked_state(self) -> None:
        """The switch excuses the missing tag, not an unreviewed working tree."""
        with tempfile.TemporaryDirectory() as directory:
            repository = self.create_repository(Path(directory), "released")
            release_notes = repository / "release-notes.txt"
            release_notes.write_text(
                release_notes.read_text(encoding="utf-8") + "Uncommitted.\n",
                encoding="utf-8",
                newline="\n",
            )
            result = self.verify(repository, allow_pending_tag=True)

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
