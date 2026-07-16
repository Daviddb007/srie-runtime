from srie.cli.commands.inspect import _build_full_tree, _inspect_identity, _inspect_runtime
from srie.sdk.client import SDK
from pathlib import Path


def test_inspect_identity(tmp_path: Path):
    sdk = SDK(str(tmp_path))
    sdk.init()
    tree = _inspect_identity(sdk)
    assert tree["label"] == "Identity"
    labels = [c["label"] for c in tree["children"]]
    assert any("Domain" in l for l in labels)


def test_inspect_runtime(tmp_path: Path):
    sdk = SDK(str(tmp_path))
    sdk.init()
    tree = _inspect_runtime(sdk)
    assert tree["label"] == "Runtime"
    labels = [c["label"] for c in tree["children"]]
    assert any("State" in l for l in labels)


def test_full_tree(tmp_path: Path):
    sdk = SDK(str(tmp_path))
    sdk.init()
    tree = _build_full_tree(sdk)
    assert tree["label"].startswith("SRIE Runtime")
    assert len(tree["children"]) == 7
