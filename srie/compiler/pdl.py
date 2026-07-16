from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml
import json

from srie.kernel.execution import ExecutionOrchestrator


KNOWN_ACTIONS = {"discover", "indicators", "diagnose", "plan", "implement", "test", "verify", "deploy", "repair"}


class PDLParseError(Exception):
    pass


class PDLProcessor:

    def __init__(self, project_path: Path):
        self._project_path = project_path
        self._orch = ExecutionOrchestrator(project_path)
        self._pdl_dir = project_path / "SDOS" / "pdl"
        self._pdl_dir.mkdir(parents=True, exist_ok=True)

    def validate(self, definition: dict) -> list[str]:
        errors = []

        if "id" not in definition:
            errors.append("Missing required field: id")
        if "goal" not in definition:
            errors.append("Missing required field: goal")

        workflows = definition.get("workflows", [])
        if not workflows:
            errors.append("At least one workflow is required")

        for i, wf in enumerate(workflows):
            wf_name = wf.get("name", f"workflow-{i}")
            steps = wf.get("steps", [])
            if not steps:
                errors.append(f"Workflow '{wf_name}' has no steps")
            for j, step in enumerate(steps):
                action = step.get("action", "")
                if action and action not in KNOWN_ACTIONS:
                    errors.append(f"Step '{step.get('name', f'step-{j}')}' in '{wf_name}': unknown action '{action}'")

        success = definition.get("success", {})
        conditions = success.get("conditions", []) if success else []
        for cond in conditions:
            if "metric" not in cond or "operator" not in cond or "value" not in cond:
                errors.append(f"Invalid success condition: {cond}")

        return errors

    def load(self, path: Path) -> dict:
        if not path.exists():
            raise PDLParseError(f"PDL file not found: {path}")
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise PDLParseError("PDL must be a YAML dictionary")
        return data

    def save(self, definition: dict) -> Path:
        path = self._pdl_dir / f"{definition.get('id', 'unnamed')}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(definition, f, default_flow_style=False, allow_unicode=True)
        return path

    def execute(self, definition: dict) -> dict:
        errors = self.validate(definition)
        if errors:
            raise PDLParseError(f"PDL validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        exec_id = definition.get("id", f"exec-pdl")
        goal = definition.get("goal", "undefined")
        priority = definition.get("priority", "medium")

        execution = self._orch.create_execution(goal, priority)
        actual_id = execution["id"]

        for wf_def in definition.get("workflows", []):
            steps = []
            for s in wf_def.get("steps", []):
                steps.append({
                    "name": s.get("name", "step"),
                    "action": s.get("action", "unknown"),
                    "params": s.get("params", {}),
                })
            self._orch.add_workflow(actual_id, wf_def.get("name", "workflow"), steps)

        self._orch.start_execution(actual_id)
        execution["pdl_id"] = exec_id

        result = {
            "execution_id": actual_id,
            "pdl_id": exec_id,
            "goal": goal,
            "workflows": len(definition.get("workflows", [])),
            "state": "RUNNING",
        }
        return result

    def list_definitions(self) -> list[dict]:
        defs = []
        for p in sorted(self._pdl_dir.glob("*.yaml")):
            with open(p, encoding="utf-8") as f:
                defs.append(yaml.safe_load(f))
        return defs

    def generate_template(self, name: str = "my-process") -> dict:
        return {
            "id": name,
            "goal": "Describe your goal here",
            "priority": "medium",
            "workflows": [
                {
                    "name": "Analysis",
                    "steps": [
                        {"name": "Discover project", "action": "discover"},
                        {"name": "Calculate indicators", "action": "indicators"},
                    ],
                },
                {
                    "name": "Execution",
                    "steps": [
                        {"name": "Implement", "action": "implement", "params": {"module": "core"}},
                        {"name": "Test", "action": "test"},
                    ],
                },
            ],
            "success": {
                "conditions": [
                    {"metric": "score", "operator": ">", "value": 85},
                ],
            },
        }
