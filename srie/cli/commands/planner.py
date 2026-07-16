from srie.modules.planner.planner import PlannerEngine
from pathlib import Path


def _plan(project_path: str) -> PlannerEngine:
    return PlannerEngine(Path(project_path).resolve())


def cmd_from_goal(project_path: str = ".", goal: str = "Build MVP", priority: str = "medium"):
    plan = _plan(project_path).plan_from_goal(goal, priority)
    print(f"Plan for: {plan['goal']}")
    print(f"  Priority: {plan['priority']}")
    print(f"  Steps: {plan['total_steps']}")
    print(f"  Estimated time: {plan.get('estimated_time_min', 0)} min")
    print(f"  Estimated cost: {plan.get('estimated_cost', 0)}")
    print(f"\nOptimized workflow:")
    for i, s in enumerate(plan['steps']):
        deps = ", ".join(s.get('depends_on', []))
        print(f"  {i+1}. [{s['action']}] {s.get('name', 'step')} ({s.get('estimated_time', 0)}m, cost: {s.get('estimated_cost', 0)})")
        if deps:
            print(f"     Depends on: {deps}")


def cmd_simulate(project_path: str = ".", goal: str = "Build MVP"):
    from srie.compiler.pdl import PDLProcessor
    pdl = PDLProcessor(Path(project_path).resolve())
    definition = pdl.generate_template(goal)
    definition["goal"] = goal
    sim = _plan(project_path).simulate(definition)
    print(f"Simulation for: {goal}")
    print(f"  Total steps: {sim['total_steps']}")
    print(f"  Sequential time: {sim['estimated_time_min']} min")
    print(f"  Parallel time: {sim['parallel_time_min']} min")
    print(f"  Time saved: {sim['time_saved_min']} min")
    print(f"  Estimated cost: {sim['estimated_cost']}")
    print(f"  Efficiency: {sim['efficiency']}%")


def cmd_execute(project_path: str = ".", goal: str = "Build MVP"):
    plan = _plan(project_path).plan_from_goal(goal)
    result = _plan(project_path).execute_plan(plan)
    print(f"Plan executed:")
    print(f"  Execution ID: {result['execution_id']}")
    print(f"  Goal: {result['goal']}")
    print(f"  Steps: {result['steps']}")
    print(f"  Est. time: {result['estimated_time_min']} min")
    print(f"  Est. cost: {result['estimated_cost']}")
    print(f"\nTrack with: srie exec status {project_path}")
