from pathlib import Path
from srie.kernel.capability import CapabilityEngine


class TestCapabilityEngine:

    def test_registry_has_builtins(self, tmp_path: Path):
        eng = CapabilityEngine(tmp_path)
        caps = eng.registry()
        assert len(caps) >= 8
        ids = [c["id"] for c in caps]
        assert "cap-discovery" in ids
        assert "cap-planner" in ids
        assert "cap-deploy" in ids

    def test_match_discovery(self, tmp_path: Path):
        eng = CapabilityEngine(tmp_path)
        matches = eng.match("discover")
        assert len(matches) >= 1
        assert matches[0]["id"] == "cap-discovery"

    def test_match_unknown(self, tmp_path: Path):
        eng = CapabilityEngine(tmp_path)
        matches = eng.match("nonexistent")
        assert len(matches) == 0

    def test_match_workflow(self, tmp_path: Path):
        eng = CapabilityEngine(tmp_path)
        steps = [
            {"name": "Discover", "action": "discover"},
            {"name": "Deploy", "action": "deploy"},
        ]
        assignments = eng.match_workflow(steps)
        assert len(assignments) == 2
        assert assignments[0]["capability"]["id"] == "cap-discovery"
        assert assignments[1]["capability"]["id"] == "cap-deploy"

    def test_required_resources(self, tmp_path: Path):
        eng = CapabilityEngine(tmp_path)
        steps = [
            {"action": "discover"},
            {"action": "indicators"},
            {"action": "deploy"},
        ]
        resources = eng.required_resources(steps)
        assert "filesystem" in resources
        assert "digital_twin" in resources
        assert "deployment" in resources
        assert "credentials" in resources

    def test_estimated_cost(self, tmp_path: Path):
        eng = CapabilityEngine(tmp_path)
        steps = [{"action": "discover"}, {"action": "indicators"}]
        cost = eng.estimated_cost(steps)
        assert cost == 2  # 1 + 1

    def test_register_custom(self, tmp_path: Path):
        eng = CapabilityEngine(tmp_path)
        eng.register({
            "name": "Custom QA",
            "actions": ["qa"],
            "resources_needed": ["test_env"],
            "cost_per_run": 4,
        })
        caps = eng.registry()
        assert len(caps) >= 9
        actions = [a for c in caps for a in c.get("actions", [])]
        assert "qa" in actions

    def test_resource_gap(self, tmp_path: Path):
        eng = CapabilityEngine(tmp_path)
        steps = [{"action": "deploy"}]
        gaps = eng.resource_gap(steps, available=["filesystem"])
        assert "deployment" in gaps
        assert "credentials" in gaps
