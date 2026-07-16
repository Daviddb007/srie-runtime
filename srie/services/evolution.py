from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json

from srie.kernel.manifest import ManifestService
from srie.services.work_log import WorkLog
from srie.services.knowledge import KnowledgeEngine


class EvolutionEngine:

    def __init__(self, project_path: Path):
        self._path = project_path
        self._manifest = ManifestService()
        self._work_log = WorkLog(project_path)
        self._knowledge = KnowledgeEngine(project_path)

    def detect_drift(self) -> list[dict]:
        drifts = []
        manifest = self._manifest.load(self._path)
        if not manifest:
            return [{"type": "STATE", "severity": "CRITICAL", "message": "Runtime not initialized"}]

        twin_path = self._path / "SDOS" / "SRIE_DIGITAL_TWIN.json"
        if twin_path.exists():
            with open(twin_path, encoding="utf-8") as f:
                twin = json.load(f)

            twin_data = twin.get("digital_twin", twin)
            indicators = twin_data.get("indicators", {})
            score = indicators.get("srie_score", 0)

            if score < 30:
                drifts.append({"type": "SCORE", "severity": "HIGH", "message": f"SRIE Score critically low: {score}", "current": score, "suggested": "Run discovery and indicators"})
            elif score < 60:
                drifts.append({"type": "SCORE", "severity": "MEDIUM", "message": f"SRIE Score below target: {score}", "current": score, "suggested": "Improve project documentation and structure"})

        dna = self._work_log.dna()
        if dna.get("total_sessions", 0) > 0:
            conf = dna.get("overall_confidence", 0)
            if conf < 0.5:
                drifts.append({"type": "CONFIDENCE", "severity": "MEDIUM", "message": f"Overall confidence low: {conf:.2f}", "current": round(conf, 2), "suggested": "Review hypothesis quality and evidence"})

        if not drifts:
            drifts.append({"type": "HEALTH", "severity": "OK", "message": "No drift detected", "current": None, "suggested": None})

        return drifts

    def suggest_evolution(self) -> dict:
        suggestions = []
        drifts = self.detect_drift()
        dna = self._work_log.dna()

        for d in drifts:
            if d["severity"] != "OK":
                suggestions.append({
                    "area": d["type"],
                    "priority": d["severity"],
                    "message": d["message"],
                    "suggested": d.get("suggested", ""),
                })

        type_dist = dna.get("type_distribution", {})
        if type_dist:
            total_acts = sum(type_dist.values())
            discovery_pct = type_dist.get("discovery", 0) / total_acts * 100 if total_acts > 0 else 0
            if discovery_pct > 70:
                suggestions.append({
                    "area": "WORK_BALANCE",
                    "priority": "LOW",
                    "message": f"Discovery dominates work ({discovery_pct:.0f}%). Consider advancing to planning and implementation.",
                    "suggested": "Define an execution goal with srie plan or srie orchestrate",
                })

        return {
            "total_suggestions": len(suggestions),
            "suggestions": suggestions,
            "dna_summary": {
                "total_sessions": dna.get("total_sessions", 0),
                "total_hypotheses": dna.get("total_hypotheses", 0),
                "confidence": dna.get("overall_confidence", 0),
            },
        }

    def auto_evolve(self) -> dict:
        suggestion = self.suggest_evolution()
        applied = []

        for s in suggestion.get("suggestions", []):
            if s.get("priority") in ("HIGH", "MEDIUM"):
                self._knowledge.extract_pattern(
                    pattern_type="evolution",
                    title=s["message"],
                    description=s.get("suggested", ""),
                    source="evolution-engine",
                    confidence=0.6,
                )
                applied.append({"area": s["area"], "action": "Pattern extracted from evolution suggestion"})

        return {
            "suggestions": suggestion["suggestions"],
            "applied": applied,
            "dna": suggestion["dna_summary"],
        }
