from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
import uuid
import hashlib


PATTERN_TYPES = ["success", "failure", "optimization", "antipattern", "reusable"]


class KnowledgeEngine:

    def __init__(self, project_path: Path):
        self._patterns_dir = project_path / "SDOS" / "knowledge" / "patterns"
        self._cases_dir = project_path / "SDOS" / "knowledge" / "cases"
        self._patterns_dir.mkdir(parents=True, exist_ok=True)
        self._cases_dir.mkdir(parents=True, exist_ok=True)
        self._journal_path = project_path / "SDOS" / "timeline.journal.md"

    def extract_pattern(self, pattern_type: str, title: str, description: str, source: str, confidence: float = 0.8) -> dict:
        pattern_id = f"pat-{uuid.uuid4().hex[:8]}"
        pattern = {
            "id": pattern_id,
            "type": pattern_type,
            "title": title,
            "description": description,
            "source": source,
            "confidence": confidence,
            "reuse_count": 0,
            "created": datetime.now(timezone.utc).isoformat(),
            "updated": datetime.now(timezone.utc).isoformat(),
            "fingerprint": hashlib.sha256(f"{pattern_type}:{title}".encode()).hexdigest()[:12],
        }
        self._save_pattern(pattern)
        self._journal(f"Pattern {pattern_id} extracted: {title} [{pattern_type}]")
        return dict(pattern)

    def store_case(self, case_type: str, action: str, outcome: str, context: dict, score: float) -> dict:
        case_id = f"case-{uuid.uuid4().hex[:8]}"
        case = {
            "id": case_id,
            "type": case_type,
            "action": action,
            "outcome": outcome,
            "context": context,
            "score": score,
            "reuse_count": 0,
            "created": datetime.now(timezone.utc).isoformat(),
        }
        self._save_case(case)
        self._journal(f"Case {case_id} stored: {action} -> {outcome} (score: {score})")
        return dict(case)

    def find_similar(self, action: str, context: dict, limit: int = 5) -> list[dict]:
        cases = self.list_cases()
        scored = []
        for c in cases:
            if c["action"] == action:
                score = self._similarity_score(c["context"], context)
                scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:limit]]

    def suggest_reuse(self, action: str, context: dict) -> dict | None:
        similar = self.find_similar(action, context, limit=1)
        if similar and similar[0].get("score", 0) > 0.5:
            case = similar[0]
            return {
                "case_id": case["id"],
                "suggested_action": case["action"],
                "expected_outcome": case["outcome"],
                "confidence": case.get("score", 0),
                "based_on": f"Similar case from {case.get('created', '?')[:10]}",
            }
        return None

    def reuse_rate(self) -> float:
        cases = self.list_cases()
        if not cases:
            return 0.0
        total = len(cases)
        reused = sum(1 for c in cases if c.get("reuse_count", 0) > 0)
        return round(reused / total * 100, 1)

    def list_patterns(self) -> list[dict]:
        patterns = []
        for p in sorted(self._patterns_dir.glob("pat-*.json")):
            with open(p, encoding="utf-8") as f:
                patterns.append(json.load(f))
        return patterns

    def list_cases(self) -> list[dict]:
        cases = []
        for p in sorted(self._cases_dir.glob("case-*.json")):
            with open(p, encoding="utf-8") as f:
                cases.append(json.load(f))
        return cases

    def _similarity_score(self, ctx_a: dict, ctx_b: dict) -> float:
        if not ctx_a or not ctx_b:
            return 0.0
        common = set(ctx_a.keys()) & set(ctx_b.keys())
        if not common:
            return 0.0
        matches = sum(1 for k in common if str(ctx_a[k]) == str(ctx_b[k]))
        return round(matches / len(common), 2)

    def _save_pattern(self, pattern: dict) -> None:
        path = self._patterns_dir / f"{pattern['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(pattern, f, indent=2, default=str)

    def _save_case(self, case: dict) -> None:
        path = self._cases_dir / f"{case['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(case, f, indent=2, default=str)

    def _journal(self, message: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()[:19].replace("T", " ")
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(f"| {ts} | {'knowledge':20s} | {message}\n")
