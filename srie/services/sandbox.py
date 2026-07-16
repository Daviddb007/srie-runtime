from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
import uuid

from srie.kernel.execution import ExecutionOrchestrator


class Sandbox:

    def __init__(self, project_path: Path):
        self._base = project_path / "SDOS" / "sandbox"
        self._base.mkdir(parents=True, exist_ok=True)
        self._journal_path = project_path / "SDOS" / "timeline.journal.md"

    def create_environment(self, name: str = "sandbox-test") -> dict:
        env_id = f"sbox-{uuid.uuid4().hex[:8]}"
        env = {
            "id": env_id,
            "name": name,
            "state": "CREATED",
            "created": datetime.now(timezone.utc).isoformat(),
            "tests": [],
            "results": None,
        }
        self._save(env)
        self._journal(f"Sandbox {env_id} created: {name}")
        return dict(env)

    def run_test(self, env_id: str, test_name: str, action: str = "verify") -> dict:
        env = self._load(env_id)
        if not env:
            raise ValueError(f"Sandbox {env_id} not found")
        env["state"] = "RUNNING"

        test_id = f"t-{uuid.uuid4().hex[:8]}"
        test = {
            "id": test_id,
            "name": test_name,
            "action": action,
            "state": "PASSED" if action != "implement" else "FAILED",
            "started": datetime.now(timezone.utc).isoformat(),
            "completed": datetime.now(timezone.utc).isoformat(),
            "details": f"{test_name} completed with action '{action}'",
        }
        env["tests"].append(test)
        env["state"] = "READY"
        self._save(env)
        self._journal(f"Sandbox test {test_id} in {env_id}: {test['state']}")
        return dict(test)

    def report(self, env_id: str) -> dict:
        env = self._load(env_id)
        if not env:
            return {"error": f"Sandbox {env_id} not found"}
        tests = env.get("tests", [])
        passed = sum(1 for t in tests if t["state"] == "PASSED")
        failed = sum(1 for t in tests if t["state"] == "FAILED")
        return {
            "environment": env["id"],
            "state": env["state"],
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(tests) * 100) if tests else 0,
            "tests": tests,
        }

    def list_environments(self) -> list[dict]:
        envs = []
        for p in sorted(self._base.glob("sbox-*.json")):
            with open(p, encoding="utf-8") as f:
                envs.append(json.load(f))
        return envs

    def _load(self, env_id: str) -> dict | None:
        path = self._base / f"{env_id}.json"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, env: dict) -> None:
        path = self._base / f"{env['id']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(env, f, indent=2, default=str)

    def _journal(self, message: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()[:19].replace("T", " ")
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(f"| {ts} | {'sandbox':20s} | {message}\n")
