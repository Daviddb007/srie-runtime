from pathlib import Path
from srie.modules.discovery.scanner import scan


def test_scan_detects_python(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    (project / "main.py").write_text("print('hello')")
    (project / "requirements.txt").write_text("flask==3.1.0\n")

    result = scan(project)
    assert len(result.languages) > 0
    assert any(l.name == "Python" for l in result.languages)
    assert result.files.total >= 2


def test_scan_returns_minimal_for_empty(tmp_path: Path):
    project = tmp_path / "empty"
    project.mkdir()
    result = scan(project)
    assert result.confidence == 0.0
    assert len(result.languages) == 0


def test_scan_detects_flask(tmp_path: Path):
    project = tmp_path / "flask-proj"
    project.mkdir()
    (project / "requirements.txt").write_text("flask==3.1.0\nclick==8.0\n")
    (project / "app.py").write_text("from flask import Flask\napp = Flask(__name__)\n")

    result = scan(project)
    assert any(fw.name == "Flask" for fw in result.frameworks)
