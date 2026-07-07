from __future__ import annotations

import os
import tempfile

from zoya.tools.project_generator import generate_project


class TestGenerateProject:
    def setup_method(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.project_dir = os.path.join(self.tmpdir, "test_project")

    def teardown_method(self) -> None:
        import shutil

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_default_template(self) -> None:
        generate_project(self.project_dir, "default")
        assert os.path.isdir(self.project_dir)
        main_file = os.path.join(self.project_dir, "main.zoya")
        assert os.path.isfile(main_file)
        with open(main_file) as f:
            content = f.read()
        assert "Hello, World!" in content

    def test_game_template(self) -> None:
        generate_project(self.project_dir, "game")
        assert os.path.isdir(os.path.join(self.project_dir, "assets"))
        assert os.path.isdir(os.path.join(self.project_dir, "sprites"))
        main_file = os.path.join(self.project_dir, "main.zoya")
        assert os.path.isfile(main_file)
        with open(main_file) as f:
            content = f.read()
        assert "Loading game" in content

    def test_ai_template(self) -> None:
        generate_project(self.project_dir, "ai")
        assert os.path.isdir(os.path.join(self.project_dir, "models"))
        assert os.path.isdir(os.path.join(self.project_dir, "data"))
        main_file = os.path.join(self.project_dir, "main.zoya")
        assert os.path.isfile(main_file)
        with open(main_file) as f:
            content = f.read()
        assert "Loading AI model" in content

    def test_web_template(self) -> None:
        generate_project(self.project_dir, "web")
        assert os.path.isdir(os.path.join(self.project_dir, "static"))
        assert os.path.isdir(os.path.join(self.project_dir, "templates"))
        main_file = os.path.join(self.project_dir, "main.zoya")
        assert os.path.isfile(main_file)
        with open(main_file) as f:
            content = f.read()
        assert "Starting web server" in content

    def test_unknown_template(self) -> None:
        generate_project(self.project_dir, "invalid")
        import shutil

        shutil.rmtree(self.project_dir, ignore_errors=True)

    def test_existing_directory(self) -> None:
        os.makedirs(self.project_dir, exist_ok=True)
        generate_project(self.project_dir, "default")
