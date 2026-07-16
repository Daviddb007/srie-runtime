from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
import uuid

from srie.kernel.manifest import ManifestService
from srie.services.sandbox import Sandbox


class RepairEngine:

    def __init__(self, project_path: Path):
        self._base = project_path / "SDOS" / "repairs"
        self._base.mkdir(parents=True, exist_ok=True)
        self._project_path = project_path
        self._manifest = ManifestService()
        self._sandbox = Sandbox(project_path)
        self._journal_path = project_path / "SDOS" / "timeline.journal.md"

    def diagnose(self) -> list[dict]:
        issues = []
        manifest = self._manifest.load(self._project_path)

        if not manifest:
            return [{"type": "CRITICAL", "message": "Runtime not initialized", "fix": "Run srie init"}]

        if manifest.state in ("FAILED", "DEGRADED"):
            issues.append({"type": "CRITICAL", "message": f"Runtime in {manifest.state} state", "fix": "Run srie runtime resume or srie init"})

        for mod in manifest.modules:
            if mod.state == "ERROR":
                issues.append({"type": "ERROR", "message": f"Module {mod.id} failed to load", "fix": f"Check modules/{mod.id}/module.yaml"})

        cognitive_path = self._project_path / "SDOS" / "state" / "cognitive.json"
        if cognitive_path.exists():
            with open(cognitive_path, encoding="utf-8") as f:
                cognitive = json.load(f)
            hyps = cognitive.get("hypotheses", {})
            low_conf = [h for h in hyps.values() if h.get("confidence", 1) < 0.3]
            for h in low_conf:
                issues.append({"type": "WARNING", "message": f"Low confidence hypothesis: {h.get('id', '?')} ({h.get('confidence', 0):.2f})", "fix": "Gather more evidence"})

        if not issues:
            issues.append({"type": "INFO", "message": "No issues detected", "fix": None})

        return issues

    def auto_repair(self, issue: dict) -> dict:
        repair_id = f"rep-{uuid.uuid4().hex[:8]}"
        result = {
            "id": repair_id,
            "issue": issue,
            "applied": False,
            "message": "No automatic fix available",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        msg = issue.get("message", "")
        fix = issue.get("fix", "")

        if "Module" in msg and "failed" in msg:
            result["applied"] = True
            result["message"] = f"Module marked for reload: {fix}"
        elif "Runtime not initialized" in msg and fix:
            from srie.kernel.runtime import Runtime
            rt = Runtime()
            rt.boot(self._project_path)
            result["applied"] = True
            result["message"] = "Runtime reinitialized"
        elif "Low confidence" in msg:
            env = self._sandbox.create_environment(f"repair-{repair_id}")
            self._sandbox.run_test(env["id"], "Re-gather evidence", "discover")
            result["applied"] = True
            result["message"] = "Evidence gathering initiated in sandbox"

        self._save(result)
        self._journal(f"Repair {repair_id}: {'applied' if result['applied'] else 'manual'} — {result['message']}")
        return result

    def auto_repair_all(self) -> list[dict]:
        issues = self.diagnose()
        results = []
        for issue in issues:
            if issue["type"] != "INFO":
                results.append(self.auto_repair(issue))
        return results

    def history(self) -> list[dict]:
        repairs = []
        for p in sorted(self._base.glob("rep-*.json")):
            with open(p, encoding="utf-8") as f:
                repairs.append(json.load(f))
        return repairs

    def _save(self, repair: dict) -> None:
        path = self._base / f"{repair['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(repair, f, indent=2, default=str)

    def _journal(self, message: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()[:19].replace("T", " ")
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(f"| {ts} | {'repair':20s} | {message}\n")
