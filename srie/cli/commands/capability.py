from srie.kernel.capability import CapabilityEngine
from pathlib import Path


def _cap(project_path: str) -> CapabilityEngine:
    return CapabilityEngine(Path(project_path).resolve())


def cmd_list(project_path: str = "."):
    caps = _cap(project_path).registry()
    print(f"Capabilities ({len(caps)}):")
    for c in caps:
        actions = ", ".join(c.get("actions", []))
        resources = ", ".join(c.get("resources_needed", []))
        print(f"  {c['id']}: {c['name']}")
        print(f"    Actions: {actions}")
        print(f"    Resources: {resources}")
        print(f"    Cost: {c.get('cost_per_run', 1)}")


def cmd_match(project_path: str = ".", action: str = "discover"):
    matches = _cap(project_path).match(action)
    if matches:
        print(f"Capabilities for action '{action}':")
        for m in matches:
            print(f"  {m['id']}: {m['name']} (cost: {m.get('cost_per_run', 1)})")
    else:
        print(f"No capability found for action '{action}'")


def cmd_plan(project_path: str = ".", goal: str = "Build MVP"):
    from srie.modules.planner.planner import PlannerEngine
    plan = PlannerEngine(Path(project_path).resolve()).plan_from_goal(goal)
    steps = plan["steps"]
    eng = _cap(project_path)
    assignments = eng.match_workflow(steps)
    resources = eng.required_resources(steps)
    cost = eng.estimated_cost(steps)

    print(f"Capability Plan for: {goal}")
    print(f"  Total steps: {len(steps)}")
    print(f"  Estimated cost: {cost}")
    print(f"  Resources needed: {', '.join(resources.keys()) if resources else 'none'}")
    print(f"\nStep assignments:")
    for a in assignments:
        step = a["step"]
        cap = a["capability"]
        cap_name = cap["name"] if cap else "UNMATCHED"
        warn = f" [WARNING: {a.get('warning', '')}]" if a.get("warning") else ""
        print(f"  {step['action']:15s} → {cap_name}{warn}")
