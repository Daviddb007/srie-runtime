from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml


class IntentState:

    def __init__(self, project_path: Path):
        self._path = project_path / "SDOS" / "state" / "intent.yaml"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._state: dict = {}
        self._load()

    def set(self, objective: str, priority: str = "medium", milestone: str | None = None) -> dict:
        self._state = {
            "objective": objective,
            "priority": priority,
            "milestone": milestone,
            "updated": datetime.now(timezone.utc).isoformat(),
        }
        self._save()
        return self._state

    def current(self) -> dict:
        if not self._state:
            return {"objective": None, "priority": None, "milestone": None}
        return dict(self._state)

    def snapshot(self) -> dict:
        return dict(self._state)

    def restore(self, data: dict) -> None:
        self._state = {k: v for k, v in data.items() if k in ("objective", "priority", "milestone", "updated")}
        self._save()

    def _load(self) -> None:
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                self._state = yaml.safe_load(f) or {}

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump(self._state, f, default_flow_style=False, allow_unicode=True)
