from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml
import uuid


class Deployment:

    def __init__(self, project_path: Path):
        self._base = project_path / "SDOS" / "deployments"
        self._base.mkdir(parents=True, exist_ok=True)
        self._journal_path = project_path / "SDOS" / "timeline.journal.md"

    def register_target(self, name: str, environment: str, url: str = "") -> dict:
        tgt_id = f"tgt-{uuid.uuid4().hex[:8]}"
        target = {
            "id": tgt_id,
            "name": name,
            "environment": environment,
            "url": url,
            "state": "REGISTERED",
            "created": datetime.now(timezone.utc).isoformat(),
            "deployments": [],
        }
        self._save_target(target)
        self._journal(f"Deployment target {tgt_id} registered: {name} ({environment})")
        return dict(target)

    def deploy(self, target_id: str, version: str = "1.0.0", artifact: str = "") -> dict:
        target = self._load_target(target_id)
        if not target:
            raise ValueError(f"Target {target_id} not found")

        dep_id = f"dep-{uuid.uuid4().hex[:8]}"
        deployment = {
            "id": dep_id,
            "target_id": target_id,
            "version": version,
            "artifact": artifact or f"build-{version}",
            "state": "DEPLOYED",
            "started": datetime.now(timezone.utc).isoformat(),
            "completed": datetime.now(timezone.utc).isoformat(),
        }
        target["deployments"].append(dep_id)
        target["state"] = "ACTIVE"
        self._save_target(target)
        self._save_deployment(deployment)
        self._journal(f"Deploy {dep_id} to {target_id}: v{version}")
        return dict(deployment)

    def rollback(self, target_id: str) -> dict:
        target = self._load_target(target_id)
        if not target:
            raise ValueError(f"Target {target_id} not found")
        deps = target.get("deployments", [])
        if len(deps) < 2:
            return {"error": "No previous version to rollback to"}
        prev_id = deps[-2]
        prev = self._load_deployment(prev_id)
        if not prev:
            return {"error": f"Previous deployment {prev_id} not found"}
        return self.deploy(target_id, prev["version"], f"rollback-{prev['version']}")

    def status(self, target_id: str) -> dict:
        target = self._load_target(target_id)
        if not target:
            return {"error": f"Target {target_id} not found"}
        deps = target.get("deployments", [])
        return {
            "target": target["name"],
            "environment": target["environment"],
            "state": target["state"],
            "total_deployments": len(deps),
            "latest_version": None,
        }

    def list_targets(self) -> list[dict]:
        targets = []
        for p in sorted(self._base.glob("tgt-*.yaml")):
            with open(p, encoding="utf-8") as f:
                targets.append(yaml.safe_load(f))
        return targets

    def _load_target(self, tgt_id: str) -> dict | None:
        path = self._base / f"{tgt_id}.yaml"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _save_target(self, target: dict) -> None:
        path = self._base / f"{target['id']}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(target, f, default_flow_style=False, allow_unicode=True)

    def _load_deployment(self, dep_id: str) -> dict | None:
        path = self._base / f"{dep_id}.yaml"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _save_deployment(self, deployment: dict) -> None:
        path = self._base / f"{deployment['id']}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(deployment, f, default_flow_style=False, allow_unicode=True)

    def _journal(self, message: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()[:19].replace("T", " ")
        with open(self._journal_path, "a", encoding="utf-8") as f:
            f.write(f"| {ts} | {'deploy':20s} | {message}\n")
