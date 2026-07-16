from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml
import json


class WorkLog:

    def __init__(self, project_path: Path):
        self._base = project_path / "SDOS" / "work"
        self._base.mkdir(parents=True, exist_ok=True)
        self._dna_path = self._base / "dna" / "session-dna.json"
        self._dna_path.parent.mkdir(parents=True, exist_ok=True)

    def consolidate(self, session_id: str, activities: list[dict]) -> dict:
        total_time = 0.0
        type_counts: dict[str, int] = {}
        total_hypotheses = 0
        total_confidence = 0.0
        activity_count = len(activities)

        for act in activities:
            atype = act.get("type", "unknown")
            type_counts[atype] = type_counts.get(atype, 0) + 1

            reasoning = act.get("reasoning", {})
            total_hypotheses += reasoning.get("hypothesis_count", 0)
            total_confidence += reasoning.get("confidence", 0)

            if act.get("started") and act.get("ended"):
                start = datetime.fromisoformat(act["started"])
                end = datetime.fromisoformat(act["ended"])
                total_time += (end - start).total_seconds()

        dna = {
            "session_id": session_id,
            "activity_count": activity_count,
            "type_distribution": type_counts,
            "total_hypotheses": total_hypotheses,
            "avg_confidence": total_confidence / activity_count if activity_count > 0 else 0,
            "total_time_seconds": total_time,
            "consolidated": datetime.now(timezone.utc).isoformat(),
        }

        existing = self._load_dna()
        existing.append(dna)
        self._save_dna(existing)
        return dna

    def dna(self) -> dict:
        all_dna = self._load_dna()
        if not all_dna:
            return {"type_distribution": {}, "total_sessions": 0, "total_hypotheses": 0}

        type_dist: dict[str, int] = {}
        total_hyp = 0
        total_sessions = len(all_dna)

        for d in all_dna:
            for atype, count in d.get("type_distribution", {}).items():
                type_dist[atype] = type_dist.get(atype, 0) + count
            total_hyp += d.get("total_hypotheses", 0)

        total_acts = sum(d.get("activity_count", 0) for d in all_dna)
        total_conf = sum(d.get("avg_confidence", 0) * d.get("activity_count", 1) for d in all_dna)

        return {
            "total_sessions": total_sessions,
            "total_activities": total_acts,
            "type_distribution": type_dist,
            "total_hypotheses": total_hyp,
            "overall_confidence": total_conf / total_acts if total_acts > 0 else 0,
        }

    def _load_dna(self) -> list[dict]:
        if not self._dna_path.exists():
            return []
        with open(self._dna_path, encoding="utf-8") as f:
            return json.load(f)

    def _save_dna(self, data: list[dict]) -> None:
        with open(self._dna_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
