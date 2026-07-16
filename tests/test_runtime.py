from pathlib import Path
from srie.kernel.runtime import Runtime

def test_runtime_boot_creates_sdos(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    rt = Runtime()
    result = rt.boot(project)
    assert (project / "SDOS" / "IDENTITY.yaml").exists()
    assert (project / "SDOS" / "REGISTRY.yaml").exists()
    assert (project / "SDOS" / "runtime.lock").exists()
    assert result.identity is not None
    assert result.manifest.state == "RUNNING"

def test_runtime_boot_on_existing(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    rt = Runtime()
    first = rt.boot(project)
    second = rt.boot(project)
    assert first.identity.domain_id == second.identity.domain_id
