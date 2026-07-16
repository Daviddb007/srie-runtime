from pathlib import Path
from srie.kernel.identity import IdentityService

def test_ensure_creates_identity(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    svc = IdentityService()
    identity = svc.ensure(project)
    assert identity.domain_id.startswith("DOM-")
    assert identity.name == "test-proj"
    assert identity.type == "standalone"
    assert identity.state == "ACTIVE"

def test_ensure_validates_existing(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    svc = IdentityService()
    first = svc.ensure(project)
    second = svc.ensure(project)
    assert first.domain_id == second.domain_id
    assert first.fingerprint == second.fingerprint
