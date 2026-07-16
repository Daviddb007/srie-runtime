from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml

from srie.sdk.models import Registry


class RegistryService:
    """Kernel service for entity registry. Pure infrastructure."""

    SDOS_DIR = "SDOS"
    REGISTRY_FILE = "REGISTRY.yaml"

    def init(self, project_path: Path) -> Registry:
        registry_path = project_path / self.SDOS_DIR / self.REGISTRY_FILE
        if registry_path.exists():
            return self.load(project_path)
        registry = Registry()
        self._save(project_path, registry)
        return registry

    def register_entity(self, project_path: Path, entity_id: str, metadata: dict) -> None:
        registry = self.load(project_path)
        registry.entities[entity_id] = {
            **metadata,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save(project_path, registry)

    def load(self, project_path: Path) -> Registry:
        registry_path = project_path / self.SDOS_DIR / self.REGISTRY_FILE
        if not registry_path.exists():
            return Registry()
        with open(registry_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        reg = data.get("registry", data)
        return Registry(
            entities=reg.get("entities", {}),
            domains=reg.get("domains", []),
            capabilities=reg.get("capabilities", []),
        )

    def _save(self, project_path: Path, registry: Registry) -> None:
        registry_path = project_path / self.SDOS_DIR / self.REGISTRY_FILE
        data = {
            "registry": {
                "entities": registry.entities,
                "domains": registry.domains,
                "capabilities": registry.capabilities,
                "updated": datetime.now(timezone.utc).isoformat(),
            }
        }
        with open(registry_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
