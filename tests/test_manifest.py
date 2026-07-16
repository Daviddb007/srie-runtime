from pathlib import Path
from srie.kernel.manifest import ManifestService

def test_manifest_create(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    (project / "SDOS").mkdir()
    svc = ManifestService()
    manifest = svc.create(project)
    assert manifest.state == "STARTING"
    assert (project / "SDOS" / "runtime.lock").exists()

def test_manifest_update(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    (project / "SDOS").mkdir()
    svc = ManifestService()
    manifest = svc.create(project)
    manifest.state = "RUNNING"
    svc.update(project, manifest)
    loaded = svc.load(project)
    assert loaded.state == "RUNNING"
