from srie.sdk.models import DigitalTwin, Node, Relationship, IndicatorReport
from srie.modules.indicators.indicators import calculate


def test_calculate_with_twin():
    twin = DigitalTwin(
        project_id="DOM-001",
        nodes=[
            Node(id="N1", type="raiz", label="Project", state="SYNCED"),
            Node(id="N2", type="dominio", label="Languages", state="SYNCED"),
            Node(id="N3", type="dominio", label="Tests", state="PENDING"),
        ],
        relationships=[Relationship(source="N1", target="N2", type="contains")],
        version=1,
    )
    report = calculate(twin)
    assert report.srie_score > 0
    assert len(report.by_domain) == 3
    assert report.confidence > 0


def test_calculate_without_twin():
    report = calculate(None)
    assert report.srie_score == 0.0
    assert report.maturity_level == "L0"
