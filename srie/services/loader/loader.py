from __future__ import annotations
from pathlib import Path
import importlib.util
import sys

from srie.services.loader.resolver import ModuleResolver
from srie.sdk.models import ModuleInfo


class ModuleLoader:

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.resolver = ModuleResolver()
        self._loaded: dict[str, object] = {}

    def load_all(self, modules_dir: Path) -> list[ModuleInfo]:
        modules = self.resolver.discover(modules_dir)
        ordered = self.resolver.resolve_dag(modules)

        loaded = []
        for mod in ordered:
            info = self._load_single(mod)
            loaded.append(info)
        return loaded

    def get_module(self, module_id: str):
        return self._loaded.get(module_id)

    def _load_single(self, mod: dict) -> ModuleInfo:
        module_path = Path(mod["_path"])
        entrypoint = module_path / mod.get("entrypoint", f"{mod['id']}.py")

        info = ModuleInfo(id=mod["id"], version=mod.get("version", "0.1.0"))

        if not entrypoint.exists():
            info.state = "ERROR"
            return info

        try:
            spec = importlib.util.spec_from_file_location(
                f"srie.modules.{mod['id']}", entrypoint
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"srie.modules.{mod['id']}"] = module
                spec.loader.exec_module(module)
                self._loaded[mod["id"]] = module
                info.state = "LOADED"
        except Exception:
            info.state = "ERROR"

        return info
