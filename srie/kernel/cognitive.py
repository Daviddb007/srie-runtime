from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json


class CognitiveState:

    def __init__(self, project_path: Path):
        self._path = project_path / "SDOS" / "state" / "cognitive.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._hypotheses: dict[str, dict] = {}
        self._load()

    def hypothesis(self, hid: str, description: str, confidence: float = 0.0, evidence_count: int = 0) -> dict:
        if hid not in self._hypotheses:
            self._hypotheses[hid] = {
                "id": hid,
                "description": description,
                "confidence": confidence,
                "evidence_count": evidence_count,
                "status": "ACTIVE",
                "created": datetime.now(timezone.utc).isoformat(),
                "updated": datetime.now(timezone.utc).isoformat(),
            }
        self._save()
        return self._hypotheses[hid]

    def validate(self, hid: str, new_evidence: int = 1) -> dict | None:
        h = self._hypotheses.get(hid)
        if not h:
            return None
        h["evidence_count"] += new_evidence
        h["confidence"] = min(1.0, h["confidence"] + 0.1 * new_evidence)
        h["updated"] = datetime.now(timezone.utc).isoformat()
        if h["confidence"] >= 0.8:
            h["status"] = "VALIDATED"
        self._save()
        return h

    def archive(self, hid: str) -> None:
        h = self._hypotheses.get(hid)
        if h:
            h["status"] = "ARCHIVED"
            h["updated"] = datetime.now(timezone.utc).isoformat()
            self._save()

    def all_active(self) -> list[dict]:
        return [h for h in self._hypotheses.values() if h["status"] == "ACTIVE"]

    def all(self) -> dict[str, dict]:
        return dict(self._hypotheses)

    def snapshot(self) -> dict:
        return {
            "hypotheses": self._hypotheses,
            "total": len(self._hypotheses),
            "active": len(self.all_active()),
            "validated": sum(1 for h in self._hypotheses.values() if h["status"] == "VALIDATED"),
            "archived": sum(1 for h in self._hypotheses.values() if h["status"] == "ARCHIVED"),
        }

    def restore(self, data: dict) -> None:
        self._hypotheses = data.get("hypotheses", {})
        self._save()

    def _load(self) -> None:
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            self._hypotheses = data.get("hypotheses", {})

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self.snapshot(), f, indent=2, default=str)
