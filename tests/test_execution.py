from pathlib import Path
from srie.kernel.execution import ExecutionOrchestrator


class TestExecutionOrchestrator:

    def test_create_execution(self, tmp_path: Path):
        o = ExecutionOrchestrator(tmp_path)
        e = o.create_execution("Build MVP", priority="high")
        assert e["state"] == "PENDING"
        assert e["goal"] == "Build MVP"
        assert e["priority"] == "high"
        assert e["id"].startswith("exec-")

    def test_execution_lifecycle(self, tmp_path: Path):
        o = ExecutionOrchestrator(tmp_path)
        e = o.create_execution("Test lifecycle")
        assert e["state"] == "PENDING"

        started = o.start_execution(e["id"])
        assert started["state"] == "RUNNING"
        assert started["started"] is not None

        completed = o.complete_execution(e["id"])
        assert completed["state"] == "COMPLETED"
        assert completed["progress"] == 100.0

    def test_add_workflow(self, tmp_path: Path):
        o = ExecutionOrchestrator(tmp_path)
        e = o.create_execution("Build with workflow")

        steps = [
            {"name": "Discover", "action": "discover"},
            {"name": "Indicators", "action": "indicators"},
        ]
        wf = o.add_workflow(e["id"], "Build Pipeline", steps)
        assert wf["id"].startswith("wf-")
        assert len(wf["steps"]) == 2
        assert wf["steps"][0]["name"] == "Discover"

    def test_step_lifecycle(self, tmp_path: Path):
        o = ExecutionOrchestrator(tmp_path)
        e = o.create_execution("Test steps")
        steps = [{"name": "Scan", "action": "discover"}]
        wf = o.add_workflow(e["id"], "Scan", steps)

        step_id = wf["steps"][0]["id"]
        o.start_step(wf["id"], step_id)
        o.complete_step(wf["id"], step_id, evidence={"files_found": 42})

        loaded_wf = o._load_workflow(wf["id"])
        step = loaded_wf["steps"][0]
        assert step["state"] == "COMPLETED"
        assert step["evidence"]["files_found"] == 42

    def test_status_summary(self, tmp_path: Path):
        o = ExecutionOrchestrator(tmp_path)
        o.create_execution("Exec 1")
        e2 = o.create_execution("Exec 2")
        o.start_execution(e2["id"])

        status = o.execution_status()
        assert status["total"] == 2
        assert status["running"] == 1
        assert status["pending"] == 1
