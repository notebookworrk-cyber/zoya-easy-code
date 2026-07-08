"""Left sidebar widget for Zoya Studio."""

from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Button, Label, ListItem, ListView, Static, Input, TabbedContent, TabPane


class LeftSidebar(Vertical):
    """Left sidebar with projects, git, and search."""

    DEFAULT_CSS = """
    LeftSidebar {
        width: 28;
        background: #161b22;
        border-right: solid #30363d;
    }

    #sidebar-header {
        height: 3;
        content-align: center middle;
        background: #0d1117;
        text-style: bold;
        color: #58a6ff;
    }

    #project-search {
        margin: 0 1;
        dock: top;
    }

    .sidebar-section-title {
        text-style: bold;
        color: #8b949e;
        padding: 1 1 0 1;
    }

    #project-list {
        height: auto;
        max-height: 20;
    }

    .project-item {
        height: 1;
        padding: 0 1;
    }

    .project-item:hover {
        background: #21262d;
    }

    Button.mini {
        width: auto;
        min-width: 12;
        margin: 0 1;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_ref = None

    def compose(self):
        yield Label("📁  ZOYA STUDIO", id="sidebar-header")

        with TabbedContent(id="sidebar-tabs"):
            with TabPane("Projects", id="tab-projects"):
                yield Input(placeholder="Search projects...", id="project-search")
                yield Button("➕ New Project", id="btn-new-project", classes="mini")
                yield Button("📂 Open", id="btn-open-project", classes="mini")
                yield Label("Recent", classes="sidebar-section-title")
                yield ListView(id="project-list")
                yield Label("Favorites", classes="sidebar-section-title")
                yield ListView(id="favorite-list")

            with TabPane("Files", id="tab-files"):
                yield Button("📄 New File", id="btn-new-file", classes="mini")
                yield Button("📁 New Folder", id="btn-new-folder", classes="mini")
                yield Label("Explorer", classes="sidebar-section-title")
                yield ListView(id="file-explorer")

            with TabPane("Git", id="tab-git"):
                yield Label("Status", classes="sidebar-section-title")
                yield Static("No changes", id="git-status")
                yield Button("💾 Commit", id="btn-git-commit", classes="mini")
                yield Button("⬆ Push", id="btn-git-push", classes="mini")
                yield Button("⬇ Pull", id="btn-git-pull", classes="mini")
                yield Button("🌿 Branch", id="btn-git-branch", classes="mini")

            with TabPane("Search", id="tab-search"):
                yield Input(placeholder="Search in files...", id="file-search-input")
                yield Button("🔍 Search", id="btn-search-files", classes="mini")
                yield ListView(id="search-results")

    def on_mount(self):
        self.app_ref = self.app

    def refresh_projects(self):
        """Refresh project lists."""
        if not hasattr(self.app, "project_manager"):
            return

        pm = self.app.project_manager

        project_list = self.query_one("#project-list", ListView)
        project_list.clear()

        for proj in pm.recent_projects[:15]:
            project_list.append(ListItem(
                Static(f"📁 {proj.name}", classes="project-item"),
                id=f"proj-{proj.path}",
            ))

        favorite_list = self.query_one("#favorite-list", ListView)
        favorite_list.clear()

        for proj in pm.favorites:
            favorite_list.append(ListItem(
                Static(f"⭐ {proj.name}", classes="project-item"),
                id=f"fav-{proj.path}",
            ))

    def refresh_files(self):
        """Refresh file explorer."""
        if not hasattr(self.app, "project_manager") or not hasattr(self.app, "file_manager"):
            return

        pm = self.app.project_manager
        fm = self.app.file_manager

        if not pm.current_project:
            return

        fm.set_directory(pm.current_project.path)
        files = fm.list_directory()

        explorer = self.query_one("#file-explorer", ListView)
        explorer.clear()

        for f in files:
            icon = "📁" if f.is_dir else "📄"
            explorer.append(ListItem(
                Static(f"{icon} {f.name}", classes="project-item"),
                id=f"file-{f.path}",
            ))

    def refresh_git(self):
        """Refresh git status."""
        if not hasattr(self.app, "git_manager"):
            return

        gm = self.app.git_manager
        if not gm.current_repo or not gm.is_git_repo():
            self.query_one("#git-status", Static).update("Not a git repository")
            return

        summary = gm.status_summary()
        total = sum(summary.values())
        if total == 0:
            self.query_one("#git-status", Static).update("✓ Working tree clean")
        else:
            status_text = (
                f"Modified: {summary['modified']}  "
                f"Added: {summary['added']}  "
                f"Deleted: {summary['deleted']}  "
                f"Untracked: {summary['untracked']}"
            )
            self.query_one("#git-status", Static).update(status_text)
