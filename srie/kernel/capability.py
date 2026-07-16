from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml
import uuid


BUILTIN_CAPABILITIES = [
    {
        "id": "cap-discovery",
        "name": "Project Discovery",
        "description": "Scans project structure, detects languages, frameworks, git state",
        "actions": ["discover"],
        "resources_needed": ["filesystem", "git"],
        "cost_per_run": 1,
    },
    {
        "id": "cap-indicators",
        "name": "Maturity Indicators",
        "description": "Calculates SRIE Score, maturity level, domain scores from Digital Twin",
        "actions": ["indicators"],
        "resources_needed": ["digital_twin"],
        "cost_per_run": 1,
    },
    {
        "id": "cap-diagnose",
        "name": "Project Diagnosis",
        "description": "Analyzes project health, identifies gaps and risks",
        "actions": ["diagnose"],
        "resources_needed": ["digital_twin", "indicators"],
        "cost_per_run": 2,
    },
    {
        "id": "cap-planner",
        "name": "Workflow Planner",
        "description": "Generates and optimizes execution plans from goals",
        "actions": ["plan"],
        "resources_needed": ["planner"],
        "cost_per_run": 2,
    },
    {
        "id": "cap-implement",
        "name": "Code Implementation",
        "description": "Generates implementation code from specifications",
        "actions": ["implement"],
        "resources_needed": ["ai", "filesystem"],
        "cost_per_run": 5,
    },
    {
        "id": "cap-test",
        "name": "Test Execution",
        "description": "Runs tests and validates implementation",
        "actions": ["test", "verify"],
        "resources_needed": ["sandbox", "filesystem"],
        "cost_per_run": 2,
    },
    {
        "id": "cap-deploy",
        "name": "Deployment",
        "description": "Deploys to target environments",
        "actions": ["deploy"],
        "resources_needed": ["deployment", "credentials"],
        "cost_per_run": 3,
    },
    {
        "id": "cap-repair",
        "name": "Auto Repair",
        "description": "Diagnoses and fixes common issues",
        "actions": ["repair"],
        "resources_needed": ["digital_twin", "ai"],
        "cost_per_run": 3,
    },
]


class CapabilityEngine:

    def __init__(self, project_path: Path):
        self._path = project_path / "SDOS" / "capabilities.yaml"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def registry(self) -> list[dict]:
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return data.get("capabilities", BUILTIN_CAPABILITIES)
        return list(BUILTIN_CAPABILITIES)

    def register(self, capability: dict) -> dict:
        caps = self.registry()
        cap_id = capability.get("id", f"cap-{uuid.uuid4().hex[:8]}")
        capability["id"] = cap_id
        capability["registered"] = datetime.now(timezone.utc).isoformat()
        caps.append(capability)
        self._save(caps)
        return capability

    def match(self, action: str) -> list[dict]:
        caps = self.registry()
        return [c for c in caps if action in c.get("actions", [])]

    def match_workflow(self, steps: list[dict]) -> list[dict]:
        result = []
        for step in steps:
            action = step.get("action", "unknown")
            matches = self.match(action)
            if matches:
                result.append({
                    "step": step,
                    "capability": matches[0],
                    "alternatives": matches[1:] if len(matches) > 1 else [],
                })
            else:
                result.append({
                    "step": step,
                    "capability": None,
                    "alternatives": [],
                    "warning": f"No capability found for action: {action}",
                })
        return result

    def required_resources(self, steps: list[dict]) -> dict:
        resources = {}
        assignments = self.match_workflow(steps)
        for a in assignments:
            cap = a.get("capability")
            if cap:
                for r in cap.get("resources_needed", []):
                    resources[r] = resources.get(r, 0) + 1
        return resources

    def estimated_cost(self, steps: list[dict]) -> int:
        total = 0
        assignments = self.match_workflow(steps)
        for a in assignments:
            cap = a.get("capability")
            if cap:
                total += cap.get("cost_per_run", 1)
        return total

    def resource_gap(self, steps: list[dict], available: list[str]) -> list[str]:
        needed = self.required_resources(steps)
        return [r for r in needed if r not in available]

    def _save(self, capabilities: list[dict]) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump({"capabilities": capabilities}, f, default_flow_style=False, allow_unicode=True)
