"""Tests for Zoya Studio file manager."""

import tempfile
from pathlib import Path

from zoya_studio.core.config import Config
from zoya_studio.core.file_manager import FileManager, FileInfo


class FakeApp:
    def __init__(self):
        self.config = Config()


def test_file_manager_list_directory():
    """Test listing directory."""
    with tempfile.TemporaryDirectory() as tmp:
        app = FakeApp()
        fm = FileManager(app)
        fm.set_directory(tmp)

        (Path(tmp) / "file.txt").write_text("hello")
        (Path(tmp) / "subdir").mkdir()

        items = fm.list_directory()
        names = {i.name for i in items}
        assert "file.txt" in names
        assert "subdir" in names


def test_file_manager_read_write():
    """Test read/write file."""
    with tempfile.TemporaryDirectory() as tmp:
        app = FakeApp()
        fm = FileManager(app)
        path = Path(tmp) / "test.txt"
        assert fm.write_file(str(path), "content")
        assert fm.read_file(str(path)) == "content"


def test_file_manager_create_delete():
    """Test create/delete file and dir."""
    with tempfile.TemporaryDirectory() as tmp:
        app = FakeApp()
        fm = FileManager(app)
        path = Path(tmp) / "new.txt"
        assert fm.create_file(str(path), "data")
        assert path.exists()
        assert fm.delete(str(path))
        assert not path.exists()


def test_file_manager_rename():
    """Test rename."""
    with tempfile.TemporaryDirectory() as tmp:
        app = FakeApp()
        fm = FileManager(app)
        old = Path(tmp) / "old.txt"
        old.write_text("x")
        assert fm.rename(str(old), "new.txt")
        assert (Path(tmp) / "new.txt").exists()
        assert not old.exists()


def test_file_manager_copy_move():
    """Test copy and move."""
    with tempfile.TemporaryDirectory() as tmp:
        app = FakeApp()
        fm = FileManager(app)
        src = Path(tmp) / "src.txt"
        src.write_text("data")
        dest = Path(tmp) / "dest.txt"
        assert fm.copy(str(src), str(dest))
        assert dest.exists()
        assert src.exists()

        moved = Path(tmp) / "moved.txt"
        assert fm.move(str(dest), str(moved))
        assert moved.exists()
        assert not dest.exists()


def test_file_manager_search():
    """Test file search."""
    with tempfile.TemporaryDirectory() as tmp:
        app = FakeApp()
        fm = FileManager(app)
        (Path(tmp) / "main.zoya").write_text("print 'hi'")
        (Path(tmp) / "other.py").write_text("x = 1")

        results = fm.search_files("main", tmp)
        assert any(r.name == "main.zoya" for r in results)


def test_file_manager_search_content():
    """Test content search."""
    with tempfile.TemporaryDirectory() as tmp:
        app = FakeApp()
        fm = FileManager(app)
        f = Path(tmp) / "code.zoya"
        f.write_text("fn hello():\n    print 'world'\n")
        results = fm.search_content("hello", tmp)
        assert any("hello" in r["content"] for r in results)


def test_file_manager_language_detection():
    """Test language detection."""
    app = FakeApp()
    fm = FileManager(app)
    assert fm.get_language("test.py") == "python"
    assert fm.get_language("test.zoya") == "zoya"
    assert fm.get_language("test.unknown") == "text"


def test_file_manager_format_size():
    """Test size formatting."""
    app = FakeApp()
    fm = FileManager(app)
    assert fm.format_size(500) == "500.0 B"
    assert "KB" in fm.format_size(2048)
