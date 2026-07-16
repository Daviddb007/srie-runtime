from pathlib import Path
from srie.modules.planner.planner import PlannerEngine


class TestPlanner:

    def test_plan_from_goal_build_mvp(self, tmp_path: Path):
        p = PlannerEngine(tmp_path)
        plan = p.plan_from_goal("Build MVP", priority="high")
        assert plan["goal"] == "Build MVP"
        assert plan["priority"] == "high"
        assert plan["total_steps"] >= 6
        assert plan["estimated_time_min"] > 0

    def test_plan_from_goal_repair(self, tmp_path: Path):
        p = PlannerEngine(tmp_path)
        plan = p.plan_from_goal("Fix critical bug")
        assert len(plan["steps"]) == 3
        assert plan["steps"][0]["action"] == "diagnose"

    def test_plan_ordering(self, tmp_path: Path):
        p = PlannerEngine(tmp_path)
        plan = p.plan_from_goal("Build MVP")
        actions = [s["action"] for s in plan["steps"]]
        assert actions.index("discover") < actions.index("indicators")
        assert actions.index("indicators") < actions.index("plan")
        assert actions.index("plan") < actions.index("implement")

    def test_simulate(self, tmp_path: Path):
        p = PlannerEngine(tmp_path)
        definition = {
            "id": "sim-test",
            "goal": "Simulate build",
            "workflows": [
                {"name": "Build", "steps": [
                    {"name": "Discover", "action": "discover"},
                    {"name": "Indicators", "action": "indicators"},
                    {"name": "Implement", "action": "implement"},
                ]},
            ],
        }
        sim = p.simulate(definition)
        assert sim["estimated_cost"] > 0
        assert sim["estimated_time_min"] > 0
        assert sim["efficiency"] >= 0

    def test_execute_plan(self, tmp_path: Path):
        p = PlannerEngine(tmp_path)
        plan = p.plan_from_goal("Quick test")
        result = p.execute_plan(plan)
        assert result["execution_id"].startswith("exec-")
        assert result["steps"] > 0
        assert result["estimated_time_min"] > 0

        from srie.kernel.execution import ExecutionOrchestrator
        orch = ExecutionOrchestrator(tmp_path)
        loaded = orch.load_execution(result["execution_id"])
        assert loaded is not None
        assert loaded["state"] == "RUNNING"
