from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml
import hashlib


class Universe:

    def __init__(self, base_path: Path):
        self._path = base_path / "SDOS" / "universe.yaml"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def ensure(self, name: str) -> dict:
        if self._path.exists():
            return self.load()
        data = {
            "universe": {
                "name": name,
                "id": f"UNI-{hashlib.sha256(name.encode()).hexdigest()[:8].upper()}",
                "created": datetime.now(timezone.utc).isoformat(),
                "updated": datetime.now(timezone.utc).isoformat(),
                "state": "ACTIVE",
                "organizations": [],
                "workspaces": [],
                "projects": [],
                "domains": [],
                "policies": {},
            }
        }
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return data

    def load(self) -> dict:
        with open(self._path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def register_organization(self, name: str) -> dict:
        data = self.load()
        orgs = data.setdefault("universe", {}).setdefault("organizations", [])
        org_id = f"ORG-{hashlib.sha256(name.encode()).hexdigest()[:8].upper()}"
        org = {"id": org_id, "name": name, "created": datetime.now(timezone.utc).isoformat(), "state": "ACTIVE"}
        if not any(o["id"] == org_id for o in orgs):
            orgs.append(org)
        data["universe"]["updated"] = datetime.now(timezone.utc).isoformat()
        self._save(data)
        return org

    def register_workspace(self, name: str, org_id: str | None = None) -> dict:
        data = self.load()
        wspaces = data.setdefault("universe", {}).setdefault("workspaces", [])
        ws_id = f"WS-{hashlib.sha256(name.encode()).hexdigest()[:8].upper()}"
        ws = {"id": ws_id, "name": name, "organization": org_id, "created": datetime.now(timezone.utc).isoformat(), "state": "ACTIVE"}
        if not any(w["id"] == ws_id for w in wspaces):
            wspaces.append(ws)
        data["universe"]["updated"] = datetime.now(timezone.utc).isoformat()
        self._save(data)
        return ws

    def register_project(self, name: str, workspace_id: str | None = None) -> dict:
        data = self.load()
        projects = data.setdefault("universe", {}).setdefault("projects", [])
        proj_id = f"PRJ-{hashlib.sha256(name.encode()).hexdigest()[:8].upper()}"
        proj = {"id": proj_id, "name": name, "workspace": workspace_id, "created": datetime.now(timezone.utc).isoformat(), "state": "ACTIVE"}
        if not any(p["id"] == proj_id for p in projects):
            projects.append(proj)
        data["universe"]["updated"] = datetime.now(timezone.utc).isoformat()
        self._save(data)
        return proj

    def register_domain(self, name: str, domain_type: str, project_id: str | None = None) -> dict:
        data = self.load()
        domains = data.setdefault("universe", {}).setdefault("domains", [])
        dom_id = f"DOM-{hashlib.sha256(name.encode()).hexdigest()[:8].upper()}"
        dom = {"id": dom_id, "name": name, "type": domain_type, "project": project_id, "created": datetime.now(timezone.utc).isoformat(), "state": "ACTIVE"}
        if not any(d["id"] == dom_id for d in domains):
            domains.append(dom)
        data["universe"]["updated"] = datetime.now(timezone.utc).isoformat()
        self._save(data)
        return dom

    def ownership_chain(self, entity_id: str) -> list[dict]:
        data = self.load()
        uni = data.get("universe", {})
        chain = [{"level": "universe", "id": uni.get("id"), "name": uni.get("name")}]

        for org in uni.get("organizations", []):
            chain.append({"level": "organization", "id": org["id"], "name": org["name"]})
            for ws in uni.get("workspaces", []):
                if ws.get("organization") == org["id"]:
                    chain.append({"level": "workspace", "id": ws["id"], "name": ws["name"]})
                    for proj in uni.get("projects", []):
                        if proj.get("workspace") == ws["id"]:
                            chain.append({"level": "project", "id": proj["id"], "name": proj["name"]})
                            for dom in uni.get("domains", []):
                                if dom.get("project") == proj["id"]:
                                    chain.append({"level": "domain", "id": dom["id"], "name": dom["name"]})
        return chain

    def twin(self) -> dict:
        if not self._path.exists():
            return {"total_organizations": 0, "total_workspaces": 0, "total_projects": 0, "total_domains": 0, "organizations": [], "workspaces": [], "projects": [], "domains": [], "state": "NOT_INITIALIZED"}
        data = self.load()
        uni = data.get("universe", {})
        orgs = uni.get("organizations", [])
        ws = uni.get("workspaces", [])
        projects = uni.get("projects", [])
        domains = uni.get("domains", [])
        return {
            "total_organizations": len(orgs),
            "total_workspaces": len(ws),
            "total_projects": len(projects),
            "total_domains": len(domains),
            "organizations": [o["name"] for o in orgs],
            "workspaces": [w["name"] for w in ws],
            "projects": [p["name"] for p in projects],
            "domains": [d["name"] for d in domains],
            "state": uni.get("state", "unknown"),
        }

    def _save(self, data: dict) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
