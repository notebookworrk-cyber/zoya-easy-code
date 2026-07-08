"""Tests for Zoya Studio git manager."""

import subprocess
import tempfile
from pathlib import Path

from zoya_studio.core.config import Config
from zoya_studio.core.git_manager import GitManager, GitFileStatus


class FakeApp:
    def __init__(self):
        self.config = Config()


def _init_git(repo_path: Path):
    """Initialize a git repo for testing."""
    try:
        subprocess.run(["git", "init", str(repo_path)], capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@zoya.dev"],
            cwd=str(repo_path), capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(repo_path), capture_output=True, check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def test_git_manager_no_git():
    """Test git manager when git unavailable."""
    app = FakeApp()
    gm = GitManager(app)
    if not gm._available:
        assert gm.status() == []
        assert not gm.is_git_repo()


def test_git_manager_init_and_status():
    """Test git init and status."""
    app = FakeApp()
    gm = GitManager(app)
    if not gm._available:
        return

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        assert _init_git(repo)
        gm.set_repo(str(repo))
        assert gm.is_git_repo()

        (repo / "file.txt").write_text("content")
        gm.add(["file.txt"])
        gm.commit("initial")

        commits = gm.log(limit=5)
        assert len(commits) >= 1
        assert "initial" in commits[0].message


def test_git_manager_branch():
    """Test branch operations."""
    app = FakeApp()
    gm = GitManager(app)
    if not gm._available:
        return

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        _init_git(repo)
        gm.set_repo(str(repo))

        assert gm.branch("feature", create=True)
        branches = gm.branch()
        assert "feature" in branches


def test_git_manager_status_summary():
    """Test status summary."""
    app = FakeApp()
    gm = GitManager(app)
    if not gm._available:
        return

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        _init_git(repo)
        gm.set_repo(str(repo))

        (repo / "new.txt").write_text("x")
        summary = gm.status_summary()
        assert summary["untracked"] >= 1
