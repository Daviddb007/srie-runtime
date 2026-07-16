from pathlib import Path
from srie.services.loader.resolver import ModuleResolver
from srie.services.loader.loader import ModuleLoader


def test_resolver_discovers_hello():
    resolver = ModuleResolver()
    modules_dir = Path(__file__).parent.parent / "srie" / "modules"
    modules = resolver.discover(modules_dir)
    ids = [m["id"] for m in modules]
    assert "hello" in ids

def test_resolver_dag_order():
    resolver = ModuleResolver()
    modules_dir = Path(__file__).parent.parent / "srie" / "modules"
    modules = resolver.discover(modules_dir)
    order = resolver.resolve_dag(modules)
    ids = [m["id"] for m in order]
    assert "hello" in ids
    assert len(order) == len(modules)

def test_loader_loads_hello(tmp_path: Path):
    project = tmp_path / "test-proj"
    project.mkdir()
    (project / "SDOS").mkdir()
    loader = ModuleLoader(project)
    modules_dir = Path(__file__).parent.parent / "srie" / "modules"
    loaded = loader.load_all(modules_dir)
    names = [m.id for m in loaded]
    assert "hello" in names
    hello_module = loader.get_module("hello")
    assert hello_module is not None
    assert hasattr(hello_module, "greet")
    assert hello_module.greet() == "Hello Module Loaded"
