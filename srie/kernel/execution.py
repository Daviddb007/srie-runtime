from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml
import uuid


EXECUTION_STATES = ["PENDING", "RUNNING", "COMPLETED", "BLOCKED", "FAILED"]
WORKFLOW_STATES = ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
STEP_STATES = ["PENDING", "RUNNING", "COMPLETED", "SKIPPED", "FAILED"]


class ExecutionOrchestrator:

    def __init__(self, project_path: Path):
        self._base = project_path / "SDOS" / "executions"
        self._base.mkdir(parents=True, exist_ok=True)
        self._journal_path = project_path / "SDOS" / "timeline.journal.md"
        self._project_path = project_path

    def create_execution(self, goal: str, priority: str = "medium") -> dict:
        exec_id = f"exec-{uuid.uuid4().hex[:8]}"
        execution = {
            "id": exec_id,
            "goal": goal,
            "priority": priority,
            "state": "PENDING",
            "progress": 0.0,
            "workflows": [],
            "created": datetime.now(timezone.utc).isoformat(),
            "updated": datetime.now(timezone.utc).isoformat(),
            "started": None,
            "completed": None,
        }
        self._save_execution(execution)
        self._journal(f"Execution {exec_id} created: {goal}")
        return dict(execution)

    def start_execution(self, exec_id: str) -> dict:
        execution = self.load_execution(exec_id)
        if not execution:
            raise ValueError(f"Execution {exec_id} not found")
        execution["state"] = "RUNNING"
        execution["started"] = datetime.now(timezone.utc).isoformat()
        execution["updated"] = datetime.now(timezone.utc).isoformat()
        self._save_execution(execution)
        self._journal(f"Execution {exec_id} started")
        return dict(execution)

    def complete_execution(self, exec_id: str) -> dict:
        execution = self.load_execution(exec_id)
        if not execution:
            raise ValueError(f"Execution {exec_id} not found")
        execution["state"] = "COMPLETED"
        execution["completed"] = datetime.now(timezone.utc).isoformat()
        execution["progress"] = 100.0
        execution["updated"] = datetime.now(timezone.utc).isoformat()
        self._save_execution(execution)
        self._journal(f"Execution {exec_id} completed")
        return dict(execution)

    def add_workflow(self, exec_id: str, name: str, steps: list[dict]) -> dict:
        execution = self.load_execution(exec_id)
        if not execution:
            raise ValueError(f"Execution {exec_id} not found")
        wf_id = f"wf-{uuid.uuid4().hex[:8]}"
        workflow = {
            "id": wf_id,
            "name": name,
            "state": "PENDING",
            "steps": [],
            "created": datetime.now(timezone.utc).isoformat(),
        }
        for i, s in enumerate(steps):
            step = {
                "id": f"step-{uuid.uuid4().hex[:8]}",
                "name": s.get("name", f"step-{i}"),
                "action": s.get("action", "unknown"),
                "state": "PENDING",
                "order": i,
                "evidence": None,
                "started": None,
                "completed": None,
            }
            workflow["steps"].append(step)
        execution["workflows"].append(wf_id)
        execution["updated"] = datetime.now(timezone.utc).isoformat()
        self._save_execution(execution)
        self._save_workflow(workflow)
        self._journal(f"Workflow {wf_id} added to execution {exec_id}: {name}")
        return dict(workflow)

    def start_step(self, wf_id: str, step_id: str) -> dict:
        wf = self._load_workflow(wf_id)
        if not wf:
            raise ValueError(f"Workflow {wf_id} not found")
        wf["state"] = "RUNNING"
        for step in wf["steps"]:
            if step["id"] == step_id:
                step["state"] = "RUNNING"
                step["started"] = datetime.now(timezone.utc).isoformat()
                break
        self._save_workflow(wf)
        self._journal(f"Step {step_id} started in workflow {wf_id}")
        return dict(wf)

    def complete_step(self, wf_id: str, step_id: str, evidence: dict | None = None) -> dict:
        wf = self._load_workflow(wf_id)
        if not wf:
            raise ValueError(f"Workflow {wf_id} not found")
        for step in wf["steps"]:
            if step["id"] == step_id:
                step["state"] = "COMPLETED"
                step["completed"] = datetime.now(timezone.utc).isoformat()
                step["evidence"] = evidence
                break
        all_done = all(s["state"] in ("COMPLETED", "SKIPPED") for s in wf["steps"])
        if all_done:
            wf["state"] = "COMPLETED"
        self._save_workflow(wf)
        self._journal(f"Step {step_id} completed in workflow {wf_id}")
        return dict(wf)

    def load_execution(self, exec_id: str) -> dict | None:
        path = self._base / f"{exec_id}.yaml"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def list_executions(self) -> list[dict]:
        executions = []
        for p in sorted(self._base.glob("exec-*.yaml")):
            with open(p, encoding="utf-8") as f:
                executions.append(yaml.safe_load(f))
        return sorted(executions, key=lambda e: e.get("created", ""), reverse=True)

    def execution_status(self) -> dict:
        all_execs = self.list_executions()
        running = [e for e in all_execs if e["state"] == "RUNNING"]
        pending = [e for e in all_execs if e["state"] == "PENDING"]
        completed = [e for e in all_execs if e["state"] == "COMPLETED"]
        blocked = [e for e in all_execs if e["state"] == "BLOCKED"]
        return {
            "total": len(all_execs),
            "running": len(running),
            "pending": len(pending),
            "completed": len(completed),
            "blocked": len(blocked),
            "active": running + pending,
        }

    def _save_execution(self, execution: dict) -> None:
        path = self._base / f"{execution['id']}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(execution, f, default_flow_style=False, allow_unicode=True)

    def _load_workflow(self, wf_id: str) -> dict | None:
        path = self._base / f"{wf_id}.yaml"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _save_workflow(self, workflow: dict) -> None:
        path = self._base / f"{workflow['id']}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(workflow, f, default_flow_style=False, allow_unicode=True)

    def _journal(self, message: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()[:19].replace("T", " ")
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(f"| {ts} | {'executor':20s} | {message}\n")
