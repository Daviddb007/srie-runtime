from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json


class Journal:

    def __init__(self, project_path: Path):
        self._path = project_path / "SDOS" / "timeline.journal.md"
        self._events_dir = project_path / "SDOS" / "state" / "events"
        self._events_dir.mkdir(parents=True, exist_ok=True)

    def append(self, event: dict) -> None:
        event["timestamp"] = event.get("timestamp", datetime.now(timezone.utc).isoformat())
        event_id = f"evt-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        event["id"] = event_id

        evt_path = self._events_dir / f"{event_id}.json"
        with open(evt_path, "w", encoding="utf-8") as f:
            json.dump(event, f, indent=2, default=str)

        with open(self._path, "a", encoding="utf-8") as f:
            ts = event["timestamp"][:19].replace("T", " ")
            source = event.get("source", "system")
            msg = event.get("message", event.get("type", "event"))
            f.write(f"| {ts} | {source:20s} | {msg}\n")

    def narrative(self, text: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()[:19].replace("T", " ")
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(f"| {ts} | {'NOTE':20s} | {text}\n")

    def replay(self, since: str | None = None) -> list[dict]:
        events = []
        for evt_file in sorted(self._events_dir.glob("evt-*.json")):
            with open(evt_file, encoding="utf-8") as f:
                evt = json.load(f)
            if since and evt.get("timestamp", "") < since:
                continue
            events.append(evt)
        return events

    def recent(self, limit: int = 10) -> list[dict]:
        all_events = sorted(self._events_dir.glob("evt-*.json"), reverse=True)
        events = []
        for evt_file in all_events[:limit]:
            with open(evt_file, encoding="utf-8") as f:
                events.append(json.load(f))
        return events
