from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json

from srie.sdk.models import DigitalTwin, Node, Relationship, IndicatorReport


class TwinRepository:

    def save(self, project_path: Path, twin: DigitalTwin) -> None:
        sdos = project_path / "SDOS"
        sdos.mkdir(exist_ok=True)

        data = {
            "digital_twin": {
                "project_id": twin.project_id,
                "version": twin.version,
                "last_sync": twin.last_sync.isoformat(),
                "metrics": twin.metrics,
                "nodes": [
                    {"id": n.id, "type": n.type, "label": n.label, "state": n.state, "metadata": n.metadata}
                    for n in twin.nodes
                ],
                "relationships": [
                    {"source": r.source, "target": r.target, "type": r.type, "weight": r.weight}
                    for r in twin.relationships
                ],
            }
        }

        if twin.indicators:
            data["digital_twin"]["indicators"] = {
                "srie_score": twin.indicators.srie_score,
                "maturity_level": twin.indicators.maturity_level,
                "by_domain": twin.indicators.by_domain,
                "confidence": twin.indicators.confidence,
                "timestamp": twin.indicators.timestamp.isoformat(),
            }

        with open(sdos / "SRIE_DIGITAL_TWIN.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, project_path: Path) -> DigitalTwin | None:
        json_path = project_path / "SDOS" / "SRIE_DIGITAL_TWIN.json"
        if not json_path.exists():
            return None
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        twin_d = data.get("digital_twin", data)
        nodes = [Node(**n) for n in twin_d.get("nodes", [])]
        relationships = [Relationship(**r) for r in twin_d.get("relationships", [])]

        indicators = None
        if "indicators" in twin_d:
            ind = twin_d["indicators"]
            indicators = IndicatorReport(
                srie_score=ind.get("srie_score", 0),
                maturity_level=ind.get("maturity_level", "L0"),
                by_domain=ind.get("by_domain", {}),
                confidence=ind.get("confidence", 0),
                timestamp=datetime.fromisoformat(ind["timestamp"]) if isinstance(ind.get("timestamp"), str) else datetime.now(timezone.utc),
            )

        return DigitalTwin(
            project_id=twin_d.get("project_id", ""),
            nodes=nodes,
            relationships=relationships,
            indicators=indicators,
            metrics=twin_d.get("metrics", {}),
            last_sync=datetime.fromisoformat(twin_d["last_sync"]) if isinstance(twin_d.get("last_sync"), str) else datetime.now(timezone.utc),
            version=twin_d.get("version", 1),
        )
