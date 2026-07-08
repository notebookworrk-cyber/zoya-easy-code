"""Git integration for Zoya Studio."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from zoya_studio.core.config import Config


@dataclass
class GitFileStatus:
    """Git file status."""

    path: str
    status: str
    staged: bool = False


@dataclass
class GitCommit:
    """Git commit info."""

    hash: str
    message: str
    author: str
    date: str
    email: str = ""


class GitManager:
    """Git integration manager."""

    def __init__(self, app: Any):
        self.app = app
        self.config = app.config if hasattr(app, "config") else Config.load()
        self.current_repo: Path | None = None
        self._available = self._check_git()

    def _check_git(self) -> bool:
        """Check if git is available."""
        try:
            subprocess.run(
                ["git", "--version"],
                capture_output=True,
                check=True,
                timeout=5,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def initialize(self) -> None:
        """Initialize git manager."""
        if hasattr(self.app, "project_manager") and self.app.project_manager.current_project:
            self.current_repo = Path(self.app.project_manager.current_project.path)

    def is_git_repo(self, path: Path | None = None) -> bool:
        """Check if path is a git repo."""
        repo = path or self.current_repo
        if not repo:
            return False
        return (repo / ".git").exists()

    def set_repo(self, path: str) -> None:
        """Set current repository."""
        self.current_repo = Path(path)

    def _run(self, args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
        """Run a git command."""
        if not self._available:
            return -1, "", "Git is not installed"

        cwd = cwd or self.current_repo
        if not cwd:
            return -1, "", "No repository set"

        try:
            result = subprocess.run(
                ["git", *args],
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def status(self) -> list[GitFileStatus]:
        """Get git status."""
        if not self.current_repo:
            return []

        code, out, err = self._run(["status", "--porcelain"])
        if code != 0:
            return []

        statuses = []
        for line in out.split("\n"):
            if not line:
                continue
            index_status = line[0]
            work_status = line[1]
            filepath = line[3:]

            if index_status != " " and index_status != "?":
                statuses.append(GitFileStatus(filepath, index_status, staged=True))
            if work_status != " ":
                statuses.append(GitFileStatus(filepath, work_status, staged=False))

        return statuses

    def status_summary(self) -> dict[str, int]:
        """Get status summary."""
        statuses = self.status()
        summary = {"modified": 0, "added": 0, "deleted": 0, "untracked": 0, "renamed": 0}
        for s in statuses:
            if s.status == "M":
                summary["modified"] += 1
            elif s.status == "A":
                summary["added"] += 1
            elif s.status == "D":
                summary["deleted"] += 1
            elif s.status == "??":
                summary["untracked"] += 1
            elif s.status == "R":
                summary["renamed"] += 1
        return summary

    def add(self, paths: list[str] | None = None) -> bool:
        """Stage files."""
        args = ["add"]
        if paths:
            args.extend(paths)
        else:
            args.append(".")
        code, _, _ = self._run(args)
        return code == 0

    def remove(self, paths: list[str], cached: bool = False) -> bool:
        """Unstage or remove files."""
        args = ["rm"]
        if cached:
            args.append("--cached")
        args.extend(paths)
        code, _, _ = self._run(args)
        return code == 0

    def commit(self, message: str, all_: bool = False) -> bool:
        """Commit changes."""
        args = ["commit", "-m", message]
        if all_:
            args.append("-a")
        code, _, _ = self._run(args)
        return code == 0

    def push(self, remote: str = "origin", branch: str | None = None) -> bool:
        """Push changes."""
        args = ["push", remote]
        if branch:
            args.append(branch)
        code, _, _ = self._run(args)
        return code == 0

    def pull(self, remote: str = "origin", branch: str | None = None) -> bool:
        """Pull changes."""
        args = ["pull", remote]
        if branch:
            args.append(branch)
        code, _, _ = self._run(args)
        return code == 0

    def fetch(self, remote: str = "origin", all_: bool = False) -> bool:
        """Fetch changes."""
        args = ["fetch", remote]
        if all_:
            args.append("--all")
        code, _, _ = self._run(args)
        return code == 0

    def branch(self, name: str | None = None, delete: bool = False) -> list[str] | bool:
        """List or create branches."""
        if name is None:
            code, out, _ = self._run(["branch", "--format=%(refname:short)"])
            if code == 0:
                return [b for b in out.split("\n") if b.strip()]
            return []
        else:
            if delete:
                code, _, _ = self._run(["branch", "-d", name])
            else:
                code, _, _ = self._run(["branch", name])
            return code == 0

    def checkout(self, ref: str, create: bool = False) -> bool:
        """Checkout a branch or commit."""
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(ref)
        code, _, _ = self._run(args)
        return code == 0

    def diff(self, path: str | None = None, cached: bool = False) -> str:
        """Get diff."""
        args = ["diff"]
        if cached:
            args.append("--cached")
        if path:
            args.append(path)
        code, out, _ = self._run(args)
        return out if code == 0 else ""

    def log(self, limit: int = 20) -> list[GitCommit]:
        """Get commit history."""
        args = [
            "log",
            f"-{limit}",
            "--format=%H%x1f%an%x1f%ae%x1f%ad%x1f%s",
            "--date=short",
        ]
        code, out, _ = self._run(args)
        if code != 0:
            return []

        commits = []
        for line in out.split("\n"):
            if not line:
                continue
            parts = line.split("\x1f")
            if len(parts) >= 5:
                commits.append(
                    GitCommit(
                        hash=parts[0],
                        author=parts[1],
                        email=parts[2],
                        date=parts[3],
                        message=parts[4],
                    )
                )
        return commits

    def stash(self, pop: bool = False, list_: bool = False) -> bool | list[str]:
        """Stash changes."""
        if list_:
            code, out, _ = self._run(["stash", "list"])
            if code == 0:
                return [line for line in out.split("\n") if line.strip()]
            return []
        elif pop:
            code, _, _ = self._run(["stash", "pop"])
        else:
            code, _, _ = self._run(["stash"])
        return code == 0

    def merge(self, branch: str) -> bool:
        """Merge a branch."""
        code, _, _ = self._run(["merge", branch])
        return code == 0

    def init(self, path: Path | None = None) -> bool:
        """Initialize a git repo."""
        code, _, _ = self._run(["init"], cwd=path or self.current_repo)
        if code == 0:
            self.current_repo = path or self.current_repo
            return True
        return False

    def get_current_branch(self) -> str:
        """Get current branch name."""
        code, out, _ = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
        if code == 0:
            return out.strip()
        return ""

    def get_remote_url(self, remote: str = "origin") -> str:
        """Get remote URL."""
        code, out, _ = self._run(["remote", "get-url", remote])
        if code == 0:
            return out.strip()
        return ""

    def configure_user(self, name: str, email: str) -> bool:
        """Configure git user."""
        code1, _, _ = self._run(["config", "user.name", name])
        code2, _, _ = self._run(["config", "user.email", email])
        if code1 == 0 and code2 == 0:
            self.config.git.user_name = name
            self.config.git.user_email = email
            self.config.save()
            return True
        return False

    def resolve_conflicts(self, path: str, resolution: str) -> bool:
        """Mark conflict resolved."""
        code, _, _ = self._run(["add", path])
        return code == 0
