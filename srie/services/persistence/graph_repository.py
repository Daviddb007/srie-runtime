from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
import yaml

from srie.sdk.models import Graph, Node, Relationship, Event


class GraphRepository:

    def save(self, project_path: Path, graph: Graph) -> None:
        sdos = project_path / "SDOS"
        sdos.mkdir(exist_ok=True)

        data = {
            "graph": {
                "version": graph.version,
                "last_updated": graph.last_updated.isoformat(),
                "nodes": [
                    {"id": n.id, "type": n.type, "label": n.label, "state": n.state, "metadata": n.metadata}
                    for n in graph.nodes
                ],
                "relationships": [
                    {"source": r.source, "target": r.target, "type": r.type, "weight": r.weight}
                    for r in graph.relationships
                ],
                "events": [
                    {"source": e.source, "type": e.type, "target": e.target, "message": e.message, "timestamp": e.timestamp.isoformat()}
                    for e in graph.events
                ],
            }
        }

        with open(sdos / "GRAPH.md", "w", encoding="utf-8") as f:
            f.write("# Project Knowledge Graph\n\n")
            f.write(f"_v{graph.version} \u2014 updated {graph.last_updated.isoformat()}_\n\n")
            f.write("```yaml\n")
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            f.write("```\n")

        with open(sdos / "GRAPH.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, project_path: Path) -> Graph | None:
        json_path = project_path / "SDOS" / "GRAPH.json"
        if not json_path.exists():
            return None
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        g = data.get("graph", data)
        return Graph(
            nodes=[Node(**n) for n in g.get("nodes", [])],
            relationships=[Relationship(**r) for r in g.get("relationships", [])],
            events=[Event(**e) for e in g.get("events", [])],
            version=g.get("version", 1),
            last_updated=datetime.fromisoformat(g["last_updated"]) if isinstance(g.get("last_updated"), str) else datetime.now(timezone.utc),
        )
