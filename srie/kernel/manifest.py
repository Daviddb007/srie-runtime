from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml

from srie.sdk.models import Manifest, ModuleInfo


class ManifestService:
    """Kernel service for runtime manifest (runtime.lock)."""

    SDOS_DIR = "SDOS"
    MANIFEST_FILE = "runtime.lock"

    def create(self, project_path: Path) -> Manifest:
        manifest = Manifest(
            runtime_version="0.1.0",
            state="STARTING",
            kernel={"identity": "pending", "registry": "pending"},
            modules=[],
        )
        self._save(project_path, manifest)
        return manifest

    def update(self, project_path: Path, manifest: Manifest) -> None:
        manifest.updated = datetime.now(timezone.utc)
        self._save(project_path, manifest)

    def load(self, project_path: Path) -> Manifest | None:
        manifest_path = project_path / self.SDOS_DIR / self.MANIFEST_FILE
        if not manifest_path.exists():
            return None
        with open(manifest_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        m = data.get("manifest", data)
        modules = [ModuleInfo(**mod) for mod in m.get("modules", [])]
        return Manifest(
            runtime_version=m.get("runtime_version", "0.1.0"),
            state=m.get("state", "STOPPED"),
            kernel=m.get("kernel", {}),
            modules=modules,
            created=datetime.fromisoformat(m["created"]) if isinstance(m.get("created"), str) else datetime.now(timezone.utc),
            updated=datetime.fromisoformat(m["updated"]) if isinstance(m.get("updated"), str) else datetime.now(timezone.utc),
            uptime_seconds=m.get("uptime_seconds", 0),
        )

    def _save(self, project_path: Path, manifest: Manifest) -> None:
        manifest_path = project_path / self.SDOS_DIR / self.MANIFEST_FILE
        data = {
            "manifest": {
                "runtime_version": manifest.runtime_version,
                "state": manifest.state,
                "kernel": manifest.kernel,
                "modules": [
                    {"id": m.id, "version": m.version, "state": m.state}
                    for m in manifest.modules
                ],
                "created": manifest.created.isoformat(),
                "updated": manifest.updated.isoformat(),
                "uptime_seconds": manifest.uptime_seconds,
            }
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
