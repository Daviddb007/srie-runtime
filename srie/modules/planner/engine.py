from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml

from srie.kernel.execution import ExecutionOrchestrator


ACTION_COSTS = {
    "discover": {"time_min": 2, "cost": 1, "deps": []},
    "indicators": {"time_min": 1, "cost": 1, "deps": ["discover"]},
    "diagnose": {"time_min": 3, "cost": 2, "deps": ["indicators"]},
    "plan": {"time_min": 2, "cost": 2, "deps": ["diagnose"]},
    "implement": {"time_min": 10, "cost": 5, "deps": ["plan"]},
    "test": {"time_min": 3, "cost": 2, "deps": ["implement"]},
    "verify": {"time_min": 2, "cost": 1, "deps": ["test"]},
    "deploy": {"time_min": 5, "cost": 3, "deps": ["verify"]},
    "repair": {"time_min": 5, "cost": 3, "deps": ["diagnose"]},
}


class PlannerEngine:

    def __init__(self, project_path: Path):
        self._project_path = project_path
        self._orch = ExecutionOrchestrator(project_path)
        self._pdl_dir = project_path / "SDOS" / "pdl"
        self._pdl_dir.mkdir(parents=True, exist_ok=True)

    def plan_from_goal(self, goal: str, priority: str = "medium") -> dict:
        workflow = self._infer_workflow(goal)
        optimized = self.optimize(workflow)
        optimized["goal"] = goal
        optimized["priority"] = priority
        optimized["estimated_time_min"] = sum(s.get("estimated_time", 0) for s in optimized["steps"])
        optimized["estimated_cost"] = sum(s.get("estimated_cost", 0) for s in optimized["steps"])
        return optimized

    def plan_from_pdl(self, pdl_def: dict) -> dict:
        workflows = pdl_def.get("workflows", [])
        all_steps = []
        for wf in workflows:
            for s in wf.get("steps", []):
                all_steps.append(s)
        optimized = self.optimize({"steps": all_steps})
        optimized["goal"] = pdl_def.get("goal", "PDL execution")
        optimized["priority"] = pdl_def.get("priority", "medium")
        optimized["estimated_time_min"] = sum(s.get("estimated_time", 0) for s in optimized["steps"])
        optimized["estimated_cost"] = sum(s.get("estimated_cost", 0) for s in optimized["steps"])
        return optimized

    def optimize(self, workflow: dict) -> dict:
        steps = list(workflow.get("steps", []))
        for step in steps:
            action = step.get("action", "unknown")
            costs = ACTION_COSTS.get(action, {"time_min": 5, "cost": 2, "deps": []})
            step["estimated_time"] = costs["time_min"]
            step["estimated_cost"] = costs["cost"]
            step["depends_on"] = [d for d in costs["deps"]]

        ordered = self._resolve_dependencies(steps)
        return {"steps": ordered, "total_steps": len(ordered)}

    def simulate(self, pdl_def: dict) -> dict:
        plan = self.plan_from_pdl(pdl_def)
        total_time = plan["estimated_time_min"]
        total_cost = plan["estimated_cost"]

        parallel_groups = self._group_parallel(plan["steps"])
        parallel_time = sum(max(s.get("estimated_time", 0) for s in group) for group in parallel_groups)

        return {
            "total_steps": plan["total_steps"],
            "estimated_time_min": total_time,
            "parallel_time_min": parallel_time,
            "time_saved_min": total_time - parallel_time,
            "estimated_cost": total_cost,
            "efficiency": round((1 - (parallel_time / total_time if total_time > 0 else 0)) * 100, 1),
            "steps": plan["steps"],
        }

    def execute_plan(self, plan: dict, exec_id: str | None = None) -> dict:
        goal = plan.get("goal", "Planned execution")
        priority = plan.get("priority", "medium")

        if exec_id:
            execution = self._orch.load_execution(exec_id)
            if not execution:
                raise ValueError(f"Execution {exec_id} not found")
        else:
            execution = self._orch.create_execution(goal, priority)
            exec_id = execution["id"]

        wf_steps = []
        for s in plan.get("steps", []):
            wf_steps.append({
                "name": s.get("name", s.get("action", "step")),
                "action": s.get("action", "unknown"),
            })

        self._orch.add_workflow(exec_id, "Planned", wf_steps)
        self._orch.start_execution(exec_id)

        return {
            "execution_id": exec_id,
            "goal": goal,
            "steps": len(wf_steps),
            "estimated_time_min": plan.get("estimated_time_min", 0),
            "estimated_cost": plan.get("estimated_cost", 0),
        }

    def _infer_workflow(self, goal: str) -> dict:
        goal_lower = goal.lower()
        steps = []

        if "mvp" in goal_lower or "build" in goal_lower:
            steps = [
                {"name": "Discover project", "action": "discover"},
                {"name": "Analyze", "action": "indicators"},
                {"name": "Diagnose", "action": "diagnose"},
                {"name": "Plan implementation", "action": "plan"},
                {"name": "Implement", "action": "implement"},
                {"name": "Test", "action": "test"},
                {"name": "Verify", "action": "verify"},
                {"name": "Deploy", "action": "deploy"},
            ]
        elif "migrate" in goal_lower:
            steps = [
                {"name": "Discover current state", "action": "discover"},
                {"name": "Analyze gaps", "action": "indicators"},
                {"name": "Plan migration", "action": "plan"},
                {"name": "Implement changes", "action": "implement"},
                {"name": "Verify", "action": "verify"},
            ]
        elif "repair" in goal_lower or "fix" in goal_lower:
            steps = [
                {"name": "Diagnose", "action": "diagnose"},
                {"name": "Repair", "action": "repair"},
                {"name": "Verify", "action": "verify"},
            ]
        else:
            steps = [
                {"name": "Discover", "action": "discover"},
                {"name": "Analyze", "action": "indicators"},
                {"name": "Plan", "action": "plan"},
            ]
        return {"steps": steps}

    def _resolve_dependencies(self, steps: list[dict]) -> list[dict]:
        available = set()
        ordered = []
        remaining = list(steps)

        while remaining:
            for step in list(remaining):
                deps = step.get("depends_on", [])
                if all(d in available for d in deps):
                    ordered.append(step)
                    available.add(step.get("action", step.get("name", "")))
                    remaining.remove(step)
            if remaining and not any(
                all(d in available for d in s.get("depends_on", []))
                for s in remaining
            ):
                ordered.extend(remaining)
                break
        return ordered

    def _group_parallel(self, steps: list[dict]) -> list[list[dict]]:
        if not steps:
            return []
        groups = [[steps[0]]]
        used_actions = {steps[0].get("action", "")}

        for step in steps[1:]:
            action = step.get("action", "")
            deps = ACTION_COSTS.get(action, {}).get("deps", [])
            can_parallel = not any(d in used_actions for d in deps)
            if can_parallel:
                groups[-1].append(step)
            else:
                groups.append([step])
            used_actions.add(action)

        return groups
