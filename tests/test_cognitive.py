from srie.services.cognitive import CognitiveService, NoOpProvider


class TestCognitive:

    def test_noop_provider(self):
        svc = CognitiveService()
        assert svc.active_provider == "noop"
        assert svc.available_providers == ["noop"]

    def test_reason(self):
        svc = CognitiveService()
        result = svc.reason("Build a SaaS")
        assert "SRIE" in result
        assert "Cognitive Provider" in result

    def test_summarize(self):
        svc = CognitiveService()
        result = svc.summarize("Long text here", max_length=5)
        assert len(result) <= 8  # 5 + "..."

    def test_plan(self):
        svc = CognitiveService()
        plans = svc.plan("Build MVP")
        assert len(plans) >= 1
        assert plans[0]["step"] == "analyze"

    def test_explain(self):
        svc = CognitiveService()
        result = svc.explain("architecture")
        assert "SRIE" in result
