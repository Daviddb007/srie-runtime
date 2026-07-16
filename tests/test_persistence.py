from pathlib import Path
from srie.services.persistence.graph_repository import GraphRepository
from srie.services.persistence.twin_repository import TwinRepository
from srie.services.persistence.report_repository import ReportRepository
from srie.sdk.models import Graph, Node, Relationship, DigitalTwin, IndicatorReport


def test_graph_repository_save_and_load(tmp_path: Path):
    project = tmp_path / "test"
    project.mkdir()
    (project / "SDOS").mkdir()

    graph = Graph(
        nodes=[Node(id="N1", type="dominio", label="Test")],
        relationships=[Relationship(source="N1", target="N2", type="contains")],
        version=1
    )

    repo = GraphRepository()
    repo.save(project, graph)
    assert (project / "SDOS" / "GRAPH.md").exists()
    assert (project / "SDOS" / "GRAPH.json").exists()

    loaded = repo.load(project)
    assert loaded is not None
    assert len(loaded.nodes) == 1
    assert loaded.nodes[0].id == "N1"


def test_twin_repository_save_and_load(tmp_path: Path):
    project = tmp_path / "test"
    project.mkdir()
    (project / "SDOS").mkdir()

    twin = DigitalTwin(
        project_id="DOM-001",
        nodes=[Node(id="N1", type="dominio")],
        relationships=[],
        version=1
    )

    repo = TwinRepository()
    repo.save(project, twin)
    assert (project / "SDOS" / "SRIE_DIGITAL_TWIN.json").exists()

    loaded = repo.load(project)
    assert loaded is not None
    assert loaded.project_id == "DOM-001"


def test_report_repository_save(tmp_path: Path):
    project = tmp_path / "test"
    project.mkdir()
    (project / "SDOS").mkdir()

    report = IndicatorReport(srie_score=74.3, maturity_level="L2", by_domain={"dev": 80}, confidence=0.9)

    repo = ReportRepository()
    repo.save(project, report)
    assert (project / "SDOS" / "SRIE_REPORT.md").exists()
    content = (project / "SDOS" / "SRIE_REPORT.md").read_text(encoding="utf-8")
    assert "74.3" in content
    assert "L2" in content
