from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml
import uuid
import json


class Activity:

    def __init__(self, project_path: Path, journal=None):
        self._base = project_path / "SDOS" / "work" / "activities"
        self._base.mkdir(parents=True, exist_ok=True)
        self._events_dir = project_path / "SDOS" / "state" / "events"
        self._journal = journal
        self._current: dict | None = None

    def begin(self, activity_type: str, objective: str, session_id: str | None = None) -> dict:
        act_id = f"act-{uuid.uuid4().hex[:8]}"
        self._current = {
            "id": act_id,
            "type": activity_type,
            "objective": objective,
            "session_id": session_id,
            "started": datetime.now(timezone.utc).isoformat(),
            "ended": None,
            "state": "RUNNING",
            "reasoning": {
                "hypothesis_count": 0,
                "confirmed": 0,
                "discarded": 0,
                "confidence": 0.0,
                "cost_usd": 0.0,
                "models": [],
                "tools": [],
            },
        }
        self._save(self._current)

        if self._journal:
            self._journal.append({
                "type": "ACTIVITY_STARTED",
                "source": f"activity:{activity_type}",
                "message": f"Activity {activity_type} started: {objective[:60]}",
                "data": {"activity_id": act_id, "session_id": session_id},
            })
        return dict(self._current)

    def complete(self, hypotheses: int = 0, confidence: float = 0.0) -> dict:
        if not self._current:
            raise RuntimeError("No active activity")
        self._current["ended"] = datetime.now(timezone.utc).isoformat()
        self._current["state"] = "COMPLETED"
        self._current["reasoning"]["hypothesis_count"] = hypotheses
        self._current["reasoning"]["confirmed"] = max(0, hypotheses - self._current["reasoning"].get("discarded", 0))
        self._current["reasoning"]["confidence"] = confidence
        self._save(self._current)

        if self._journal:
            self._journal.append({
                "type": "ACTIVITY_COMPLETED",
                "source": f"activity:{self._current['type']}",
                "message": f"Activity {self._current['type']} completed — {hypotheses} hypotheses, confidence {confidence:.2f}",
                "data": {"activity_id": self._current["id"]},
            })

        result = dict(self._current)
        self._current = None
        return result

    def reasoning(self, **kwargs) -> dict:
        if not self._current:
            raise RuntimeError("No active activity")
        for key, value in kwargs.items():
            if key in self._current["reasoning"]:
                self._current["reasoning"][key] = value
        self._save(self._current)
        return dict(self._current)

    def replay(self, activity_id: str | None = None) -> list[dict]:
        aid = activity_id or (self._current["id"] if self._current else None)
        if not aid:
            return []
        events = []
        for evt_file in sorted(self._events_dir.glob("evt-*.json")):
            with open(evt_file, encoding="utf-8") as f:
                evt = json.load(f)
            evt_data = evt.get("data", {})
            if evt_data.get("activity_id") == aid or evt.get("source", "").startswith(f"activity:{aid}"):
                events.append(evt)
        return events

    def current(self) -> dict | None:
        return dict(self._current) if self._current else None

    def load(self, activity_id: str) -> dict | None:
        path = self._base / f"{activity_id}.yaml"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _save(self, data: dict) -> None:
        path = self._base / f"{data['id']}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
