from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml

from srie.sdk.models import IndicatorReport


class ReportRepository:

    def save(self, project_path: Path, report: IndicatorReport) -> None:
        sdos = project_path / "SDOS"
        sdos.mkdir(exist_ok=True)

        data = {
            "srie_report": {
                "srie_score": report.srie_score,
                "maturity_level": report.maturity_level,
                "by_domain": report.by_domain,
                "confidence": report.confidence,
                "timestamp": report.timestamp.isoformat(),
                "trends": report.trends or {},
            }
        }

        content = [
            "# SRIE Report",
            "",
            f"**Score:** {report.srie_score}",
            f"**Maturity:** {report.maturity_level}",
            f"**Confidence:** {report.confidence:.2f}",
            f"**Date:** {report.timestamp.isoformat()}",
            "",
            "```yaml",
        ]

        yaml_str = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        content.append(yaml_str.rstrip())
        content.append("```")
        content.append("")
        content.append("## Per-Domain Scores")
        content.append("")

        for domain, score in sorted(report.by_domain.items()):
            bar = chr(9608) * int(score / 10) + chr(9617) * (10 - int(score / 10))
            content.append(f"- **{domain}:** {score:.1f} {bar}")

        with open(sdos / "SRIE_REPORT.md", "w", encoding="utf-8") as f:
            f.write("\n".join(content))
