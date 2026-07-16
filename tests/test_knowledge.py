from pathlib import Path
from srie.services.knowledge import KnowledgeEngine
from srie.services.evolution import EvolutionEngine


class TestKnowledge:

    def test_extract_pattern(self, tmp_path: Path):
        k = KnowledgeEngine(tmp_path)
        p = k.extract_pattern("success", "Flask detected", "Found Flask in requirements", "discovery", 0.95)
        assert p["type"] == "success"
        assert p["title"] == "Flask detected"
        assert p["confidence"] == 0.95

    def test_store_case(self, tmp_path: Path):
        k = KnowledgeEngine(tmp_path)
        c = k.store_case("execution", "discover", "success", {"lang": "python"}, 0.9)
        assert c["action"] == "discover"
        assert c["outcome"] == "success"

    def test_find_similar(self, tmp_path: Path):
        k = KnowledgeEngine(tmp_path)
        k.store_case("execution", "discover", "success", {"lang": "python", "framework": "flask"}, 0.9)
        k.store_case("execution", "discover", "failure", {"lang": "python", "framework": "django"}, 0.3)
        similar = k.find_similar("discover", {"lang": "python", "framework": "flask"})
        assert len(similar) >= 1
        assert similar[0]["outcome"] == "success"

    def test_suggest_reuse(self, tmp_path: Path):
        k = KnowledgeEngine(tmp_path)
        k.store_case("execution", "discover", "success", {"lang": "python"}, 0.9)
        suggestion = k.suggest_reuse("discover", {"lang": "python"})
        assert suggestion is not None
        assert suggestion["expected_outcome"] == "success"

    def test_reuse_rate(self, tmp_path: Path):
        k = KnowledgeEngine(tmp_path)
        assert k.reuse_rate() == 0.0
        k.store_case("execution", "discover", "success", {}, 0.9)
        assert k.reuse_rate() >= 0

    def test_list_patterns(self, tmp_path: Path):
        k = KnowledgeEngine(tmp_path)
        k.extract_pattern("success", "Test", "", "manual")
        assert len(k.list_patterns()) == 1


class TestEvolution:

    def test_detect_drift_uninitialized(self, tmp_path: Path):
        e = EvolutionEngine(tmp_path)
        drifts = e.detect_drift()
        assert len(drifts) > 0

    def test_suggest_evolution(self, tmp_path: Path):
        e = EvolutionEngine(tmp_path)
        suggestion = e.suggest_evolution()
        assert "suggestions" in suggestion
        assert "dna_summary" in suggestion

    def test_auto_evolve(self, tmp_path: Path):
        e = EvolutionEngine(tmp_path)
        result = e.auto_evolve()
        assert "applied" in result
        assert "suggestions" in result
