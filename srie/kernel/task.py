from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml
import uuid


VALID_TRANSITIONS = {
    "PENDING": ["RUNNING"],
    "RUNNING": ["COMPLETED", "BLOCKED", "FAILED", "RESUMABLE"],
    "COMPLETED": [],
    "FAILED": ["PENDING"],
    "BLOCKED": ["RUNNING", "WAITING_INPUT"],
    "WAITING_INPUT": ["RUNNING", "COMPLETED"],
    "DELEGATED": ["COMPLETED", "FAILED"],
    "RESUMABLE": ["RUNNING"],
}


class Task:

    def __init__(self, project_path: Path):
        self._base = project_path / "SDOS" / "work" / "tasks"
        self._base.mkdir(parents=True, exist_ok=True)

    def create(self, name: str, activity_id: str | None = None, depends_on: list[str] | None = None) -> dict:
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        task = {
            "id": task_id,
            "name": name,
            "activity_id": activity_id,
            "state": "PENDING",
            "depends_on": depends_on or [],
            "created": datetime.now(timezone.utc).isoformat(),
            "updated": datetime.now(timezone.utc).isoformat(),
            "result": None,
        }
        self._save(task)
        return dict(task)

    def transition(self, task_id: str, target_state: str) -> dict:
        task = self.load(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        current = task["state"]
        allowed = VALID_TRANSITIONS.get(current, [])

        if current == "PENDING" and target_state == "RUNNING":
            deps = task.get("depends_on", [])
            for dep_id in deps:
                dep = self.load(dep_id)
                if dep and dep["state"] != "COMPLETED":
                    raise ValueError(f"Dependency {dep_id} not completed (state: {dep['state']})")

        if target_state not in allowed:
            raise ValueError(f"Invalid transition: {current} -> {target_state}")

        task["state"] = target_state
        task["updated"] = datetime.now(timezone.utc).isoformat()
        self._save(task)
        return dict(task)

    def load(self, task_id: str) -> dict | None:
        path = self._base / f"{task_id}.yaml"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def list_by_activity(self, activity_id: str) -> list[dict]:
        tasks = []
        for p in self._base.glob("task-*.yaml"):
            with open(p, encoding="utf-8") as f:
                task = yaml.safe_load(f)
            if task.get("activity_id") == activity_id:
                tasks.append(task)
        return sorted(tasks, key=lambda t: t.get("created", ""))

    def _save(self, task: dict) -> None:
        path = self._base / f"{task['id']}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(task, f, default_flow_style=False, allow_unicode=True)
