from pathlib import Path
from srie.compiler.pdl import PDLProcessor, PDLParseError


class TestPDL:

    def test_validate_valid(self, tmp_path: Path):
        proc = PDLProcessor(tmp_path)
        definition = {
            "id": "exec-test",
            "goal": "Build test",
            "priority": "high",
            "workflows": [
                {"name": "Analysis", "steps": [{"name": "Discover", "action": "discover"}]},
            ],
            "success": {"conditions": [{"metric": "score", "operator": ">", "value": 85}]},
        }
        errors = proc.validate(definition)
        assert len(errors) == 0

    def test_validate_missing_goal(self, tmp_path: Path):
        proc = PDLProcessor(tmp_path)
        definition = {"id": "exec-test", "workflows": []}
        errors = proc.validate(definition)
        assert len(errors) > 0
        assert any("goal" in e for e in errors)

    def test_validate_unknown_action(self, tmp_path: Path):
        proc = PDLProcessor(tmp_path)
        definition = {
            "id": "exec-test",
            "goal": "Test",
            "workflows": [{"name": "W1", "steps": [{"name": "Bad", "action": "nonexistent"}]}],
        }
        errors = proc.validate(definition)
        assert any("unknown action" in e for e in errors)

    def test_execute_creates_execution(self, tmp_path: Path):
        proc = PDLProcessor(tmp_path)
        definition = {
            "id": "exec-build-mvp",
            "goal": "Build MVP",
            "workflows": [
                {"name": "Analysis", "steps": [
                    {"name": "Discover", "action": "discover"},
                    {"name": "Indicators", "action": "indicators"},
                ]},
            ],
        }
        result = proc.execute(definition)
        assert result["state"] == "RUNNING"
        assert result["goal"] == "Build MVP"
        assert result["workflows"] == 1

        # Verify execution exists in orchestrator
        from srie.kernel.execution import ExecutionOrchestrator
        orch = ExecutionOrchestrator(tmp_path)
        loaded = orch.load_execution(result["execution_id"])
        assert loaded is not None
        assert loaded["goal"] == "Build MVP"

    def test_save_and_load(self, tmp_path: Path):
        proc = PDLProcessor(tmp_path)
        definition = {"id": "exec-saved", "goal": "Saved test", "workflows": []}
        path = proc.save(definition)
        assert path.exists()

        loaded = proc.load(path)
        assert loaded["id"] == "exec-saved"

    def test_template_generation(self, tmp_path: Path):
        proc = PDLProcessor(tmp_path)
        template = proc.generate_template("my-process")
        assert template["id"] == "my-process"
        assert len(template["workflows"]) == 2
        assert template["workflows"][0]["steps"][0]["action"] == "discover"

    def test_invalid_file(self, tmp_path: Path):
        proc = PDLProcessor(tmp_path)
        import pytest
        with pytest.raises(PDLParseError, match="not found"):
            proc.load(tmp_path / "nonexistent.yaml")
