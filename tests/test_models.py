from pathlib import Path
from srie.sdk.models import Identity

def test_identity_defaults():
    identity = Identity(domain_id="DOM-001", name="Test", type="standalone", version="1.0.0")
    assert identity.state == "ACTIVE"
    assert identity.fingerprint.startswith("sha256:")

def test_identity_fingerprint_stable():
    i1 = Identity(domain_id="DOM-001", name="Test", type="standalone", version="1.0.0")
    i2 = Identity(domain_id="DOM-001", name="Test", type="standalone", version="1.0.0")
    assert i1.fingerprint == i2.fingerprint
