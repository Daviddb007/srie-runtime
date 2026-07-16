from __future__ import annotations
from srie.sdk.models import IndicatorReport, DigitalTwin


def calculate(twin: DigitalTwin | None) -> IndicatorReport:
    report = IndicatorReport()

    if not twin:
        return report

    total = len(twin.nodes)
    synced = sum(1 for n in twin.nodes if n.state == "SYNCED")

    if total > 0:
        report.srie_score = (synced / total) * 100
    else:
        report.srie_score = 0.0

    report.by_domain = {n.label or n.type: 50.0 for n in twin.nodes}
    report.confidence = 0.7 if total > 0 else 0.0

    if report.srie_score >= 90:
        report.maturity_level = "L5"
    elif report.srie_score >= 70:
        report.maturity_level = "L3"
    elif report.srie_score >= 50:
        report.maturity_level = "L2"
    elif report.srie_score >= 20:
        report.maturity_level = "L1"
    else:
        report.maturity_level = "L0"

    return report
