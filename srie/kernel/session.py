from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml
import uuid


class Session:

    def __init__(self, project_path: Path):
        self._base = project_path / "SDOS" / "work" / "sessions"
        self._base.mkdir(parents=True, exist_ok=True)
        self._current: dict | None = None

    def start(self, user: str = "system") -> dict:
        session_id = f"ses-{uuid.uuid4().hex[:8]}"
        self._current = {
            "id": session_id,
            "user": user,
            "started": datetime.now(timezone.utc).isoformat(),
            "ended": None,
            "duration_seconds": None,
            "activity_count": 0,
            "state": "ACTIVE",
        }
        self._save(self._current)
        return dict(self._current)

    def end(self) -> dict:
        if not self._current:
            latest = self.latest()
            if latest and latest.get("state") == "ACTIVE":
                self._current = latest
            else:
                raise RuntimeError("No active session found")
        now = datetime.now(timezone.utc)
        start = datetime.fromisoformat(self._current["started"])
        self._current["ended"] = now.isoformat()
        self._current["duration_seconds"] = int((now - start).total_seconds())
        self._current["state"] = "COMPLETED"
        self._save(self._current)
        result = dict(self._current)
        self._current = None
        return result

    def current(self) -> dict | None:
        if self._current:
            return dict(self._current)
        latest = self.latest()
        if latest and latest.get("state") == "ACTIVE":
            self._current = latest
            return dict(latest)
        return None

    def latest(self) -> dict | None:
        index = self._load_index()
        if not index:
            return None
        latest_id = max(s["id"] for s in index)
        return self.load(latest_id)

    def load(self, session_id: str) -> dict | None:
        path = self._base / f"{session_id}.yaml"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def list_all(self) -> list[dict]:
        return self._load_index()

    def _save(self, data: dict) -> None:
        path = self._base / f"{data['id']}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        self._update_index(data["id"])

    def _load_index(self) -> list[dict]:
        index_path = self._base / "INDEX.yaml"
        if not index_path.exists():
            return []
        with open(index_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("sessions", [])

    def _update_index(self, session_id: str) -> None:
        index = self._load_index()
        if not any(s["id"] == session_id for s in index):
            index.append({"id": session_id, "updated": datetime.now(timezone.utc).isoformat()})
        with open(self._base / "INDEX.yaml", "w", encoding="utf-8") as f:
            yaml.dump({"sessions": index}, f, default_flow_style=False, allow_unicode=True)
