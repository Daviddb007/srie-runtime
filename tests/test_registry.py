from pathlib import Path
from srie.kernel.registry import RegistryService

def test_registry_init_creates_file(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    (project / "SDOS").mkdir()
    svc = RegistryService()
    registry = svc.init(project)
    assert (project / "SDOS" / "REGISTRY.yaml").exists()

def test_registry_register_entity(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    (project / "SDOS").mkdir()
    svc = RegistryService()
    svc.init(project)
    svc.register_entity(project, "module:discovery", {"version": "1.0.0", "state": "LOADED"})
    loaded = svc.load(project)
    assert "module:discovery" in loaded.entities
