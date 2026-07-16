from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml


class Workspace:

    def __init__(self, project_path: Path):
        self._path = project_path / "SDOS" / "work" / "workspace.yaml"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def ensure(self, name: str, organization: str | None = None) -> dict:
        if self._path.exists():
            return self.load()
        data = {
            "workspace": {
                "name": name,
                "organization": organization,
                "created": datetime.now(timezone.utc).isoformat(),
                "updated": datetime.now(timezone.utc).isoformat(),
                "state": "ACTIVE",
                "projects": [],
                "domains": [],
                "policies": {},
            }
        }
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return data

    def load(self) -> dict:
        with open(self._path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
