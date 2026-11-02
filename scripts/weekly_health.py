#!/usr/bin/env python3
"""Weekly health check for Kevin's public repositories.

Runs inside GitHub Actions with the workflow's GITHUB_TOKEN (read-only, public
data only) and needs nothing but the Python standard library. For each
repository it reports:

* CI: the latest completed run of every workflow on ``main``;
* open pull requests (drafts excluded) and open issues;
* the commits of the last ``--days`` days: added lines that look like an API
  key or token, absolute local paths such as ``C:\\Users\\kevin``, and new code
  comments or commit subjects that look Spanish.

The Markdown report goes to ``$GITHUB_STEP_SUMMARY`` (or stdout). The script
exits with status 1 when anything needs attention, so the workflow turns red
and GitHub emails the owner; a clean week stays green and silent.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field

OWNER = "LiriothTeltanion"
REPOS = (
    "NovaMusicLab",
    "IvritSheli",
    "Fullstack2026",
    "ezriva",
    "NovaFit",
    "Jetstream89",
    "ChristopherRodriguezCVOnline",
    "LiriothTeltanion",
    "CV",
    "bitpip-privacy",
)
FAILED_CONCLUSIONS = {"failure", "timed_out", "startup_failure"}
STALE_PR_DAYS = 14

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}|\bgithub_pat_[A-Za-z0-9_]{40,}"),
    "Anthropic key": re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}"),
    "OpenAI key": re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"),
    "AWS key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "Slack token": re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"),
    "database URL with password": re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s:/@'\"]+:[^\s@'\"<>{}$]{4,}@"
        r"(?!localhost|127\.0\.0\.1|db\b|postgres\b|example|<)[^\s'\"]+"
    ),
}
LOCAL_PATH = re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]+kevin\b")
COMMENT = re.compile(r"^\s*(?:#|//|/?\*|<!--|\{/\*)\s?(.*)")
SPANISH_WORDS = re.compile(
    r"\b(de|la|el|en|y|que|los|las|se|un|una|del|al|por|con|para|es|lo|su|como|pero|sin|esta|este|son|hay|cada|desde|hasta|antes|ahora|solo)\b",
    re.IGNORECASE,
)
ENGLISH_WORDS = re.compile(r"\b(the|and|is|are|to|of|with|for|this|that|it|on|in|be|by|not|or|an|as|from)\b", re.IGNORECASE)
CODE_EXTENSIONS = (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".css", ".yml", ".yaml", ".toml", ".sh", ".ps1", ".sql")


def mask(value: str) -> str:
    """Show only the first characters of a suspected secret.

    >>> mask("sk-ant-abcdefghijklmnopqrstuvwxyz")
    'sk-ant…(33 chars)'
    """
    value = value.strip()
    return value[:6] + f"…({len(value)} chars)"


def looks_spanish(text: str) -> bool:
    """True when a sentence reads as Spanish rather than English.

    >>> looks_spanish("Arregla el error de los catalogos para que no fallen")
    True
    >>> looks_spanish("Fix the catalog error so the tests pass")
    False
    """
    spanish = len(SPANISH_WORDS.findall(text))
    english = len(ENGLISH_WORDS.findall(text))
    return spanish >= 3 and spanish > english * 1.2


def scan_added_lines(filename: str, patch: str) -> list[str]:
    """Findings for the added lines of one file's diff."""
    findings: list[str] = []
    is_code = filename.lower().endswith(CODE_EXTENSIONS)
    for line in patch.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        text = line[1:]
        for kind, pattern in SECRET_PATTERNS.items():
            match = pattern.search(text)
            if match:
                findings.append(f"possible {kind} in `{filename}`: `{mask(match.group(0))}`")
        if LOCAL_PATH.search(text):
            findings.append(f"absolute local path in `{filename}`")
        comment = COMMENT.match(text)
        if is_code and comment and looks_spanish(comment.group(1)):
            findings.append(f"Spanish code comment in `{filename}`")
    return findings


@dataclass
class RepoReport:
    name: str
    ci: str = "?"
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class GitHub:
    def __init__(self, token: str | None) -> None:
        self.token = token

    def get(self, path: str):
        request = urllib.request.Request(
            f"https://api.github.com{path}",
            headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
        )
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)


def check_repo(gh: GitHub, repo: str, since: dt.datetime, now: dt.datetime) -> RepoReport:
    report = RepoReport(repo)
    base = f"/repos/{OWNER}/{repo}"

    # Only workflows that still exist count; a deleted workflow's last red run
    # would otherwise stay "failing" forever.
    active = {
        w["id"]: w["path"]
        for w in gh.get(f"{base}/actions/workflows?per_page=100").get("workflows", [])
        if w.get("state") == "active"
    }
    runs = gh.get(f"{base}/actions/runs?branch=main&per_page=50&exclude_pull_requests=true").get("workflow_runs", [])
    latest: dict[int, dict] = {}
    for run in runs:
        if run.get("status") == "completed" and run["workflow_id"] in active and run["workflow_id"] not in latest:
            latest[run["workflow_id"]] = run
    failed = []
    for run in latest.values():
        if run.get("conclusion") not in FAILED_CONCLUSIONS:
            continue
        if active[run["workflow_id"]].startswith("dynamic/dependabot"):
            # A Dependabot update job that could not produce a PR, usually a
            # fix that needs a major version. Worth knowing, not a broken build.
            report.notes.append(f"Dependabot could not open an update: {run['name']}")
        else:
            failed.append(run["name"])
    if not latest:
        report.ci = "no runs"
    elif failed:
        report.ci = "red"
        report.problems.extend(f"CI failing on main: {name}" for name in failed)
    else:
        report.ci = "green"

    for pr in gh.get(f"{base}/pulls?state=open&per_page=100"):
        if pr.get("draft"):
            continue
        created = dt.datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
        age = (now - created).days
        label = f"PR #{pr['number']} \"{pr['title']}\" open for {age} days"
        if age >= STALE_PR_DAYS:
            report.problems.append(label)
        else:
            report.notes.append(label)
    issues = [i for i in gh.get(f"{base}/issues?state=open&per_page=100") if "pull_request" not in i]
    for issue in issues:
        report.problems.append(f"open issue #{issue['number']} \"{issue['title']}\"")

    commits = gh.get(f"{base}/commits?sha=main&since={since.strftime('%Y-%m-%dT%H:%M:%SZ')}&per_page=50")
    for commit in commits:
        subject = commit["commit"]["message"].splitlines()[0]
        if looks_spanish(subject):
            report.problems.append(f"Spanish commit subject {commit['sha'][:7]}: \"{subject[:70]}\"")
        detail = gh.get(f"{base}/commits/{commit['sha']}")
        for changed in detail.get("files", []):
            for finding in scan_added_lines(changed["filename"], changed.get("patch", "")):
                report.problems.append(f"{finding} (commit {commit['sha'][:7]})")
    report.notes.append(f"{len(commits)} commit(s) checked since {since.date()}")
    return report


def render(reports: list[RepoReport], days: int) -> str:
    total = sum(len(r.problems) for r in reports)
    lines = [
        f"# Weekly GitHub health check — {dt.date.today().isoformat()}",
        "",
        "✅ Everything is green and clean." if total == 0 else f"⚠️ {total} item(s) need attention.",
        "",
        "| Repository | CI on main | Needs attention | Notes |",
        "|---|---|---:|---|",
    ]
    for r in reports:
        lines.append(f"| {r.name} | {r.ci} | {len(r.problems)} | {'; '.join(r.notes) or '—'} |")
    for r in reports:
        if r.problems:
            lines += ["", f"## {r.name}", *[f"- {p}" for p in r.problems]]
    lines += ["", f"_Window: last {days} days. Read-only check; nothing was changed._"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=8, help="how many days of commits to scan")
    args = parser.parse_args(argv)

    gh = GitHub(os.environ.get("GITHUB_TOKEN"))
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=args.days)
    reports: list[RepoReport] = []
    for repo in REPOS:
        try:
            reports.append(check_repo(gh, repo, since, now))
        except urllib.error.URLError as error:
            failed = RepoReport(repo, ci="error")
            failed.problems.append(f"could not read the repository: {error}")
            reports.append(failed)

    text = render(reports, args.days)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(text)
    print(text)
    return 1 if any(r.problems for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
