from __future__ import annotations
from pathlib import Path
import yaml


class ModuleResolver:

    def discover(self, modules_dir: Path) -> list[dict]:
        modules = []
        if not modules_dir.exists():
            return modules
        for module_dir in sorted(modules_dir.iterdir()):
            if not module_dir.is_dir():
                continue
            yaml_path = module_dir / "module.yaml"
            if yaml_path.exists():
                with open(yaml_path, encoding="utf-8") as f:
                    mod = yaml.safe_load(f)
                mod["_path"] = str(module_dir)
                modules.append(mod)
        return modules

    def resolve_dag(self, modules: list[dict]) -> list[dict]:
        graph: dict[str, list[str]] = {}
        for mod in modules:
            mid = mod["id"]
            deps = mod.get("depends_on", []) or []
            graph[mid] = [d for d in deps if any(m2["id"] == d for m2 in modules)]

        in_degree: dict[str, int] = {}
        for mid, deps in graph.items():
            in_degree[mid] = len(deps)
            for dep in deps:
                in_degree.setdefault(dep, 0)

        queue = [mid for mid, deg in in_degree.items() if deg == 0]
        result: list[dict] = []
        while queue:
            node = queue.pop(0)
            result.append([m for m in modules if m["id"] == node][0])
            for mid, deps in graph.items():
                if node in deps:
                    in_degree[mid] -= 1
                    if in_degree[mid] == 0:
                        queue.append(mid)

        if len(result) != len(modules):
            unresolved = set(m["id"] for m in modules) - set(r["id"] for r in result)
            raise ValueError(f"Circular dependency detected in modules: {unresolved}")
        return result
