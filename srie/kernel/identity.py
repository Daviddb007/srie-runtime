from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import yaml

from srie.sdk.models import Identity


class IdentityService:
    """Kernel service for project identity."""

    SDOS_DIR = "SDOS"
    IDENTITY_FILE = "IDENTITY.yaml"

    def ensure(self, project_path: Path) -> Identity:
        identity_path = project_path / self.SDOS_DIR / self.IDENTITY_FILE
        if identity_path.exists():
            return self._load(identity_path)
        return self._create(project_path)

    def whoami(self, project_path: Path) -> Identity | None:
        identity_path = project_path / self.SDOS_DIR / self.IDENTITY_FILE
        if identity_path.exists():
            return self._load(identity_path)
        return None

    def _create(self, project_path: Path) -> Identity:
        sdos_path = project_path / self.SDOS_DIR
        sdos_path.mkdir(parents=True, exist_ok=True)

        identity = Identity(
            domain_id=f"DOM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{abs(hash(project_path.name)) % 10000:04d}",
            name=project_path.name,
            type="standalone",
            version="1.0.0",
        )

        self._save(project_path, identity)
        return identity

    def _load(self, identity_path: Path) -> Identity:
        with open(identity_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        ident = data.get("identity", data)
        return Identity(
            domain_id=ident["domain_id"],
            name=ident["name"],
            type=ident.get("type", "standalone"),
            version=ident.get("version", "1.0.0"),
            state=ident.get("state", "ACTIVE"),
            organization=ident.get("organization"),
            authority=ident.get("authority"),
            fingerprint=ident.get("fingerprint", ""),
            created=datetime.fromisoformat(ident["created"]) if isinstance(ident.get("created"), str) else datetime.now(timezone.utc),
            updated=datetime.fromisoformat(ident["updated"]) if isinstance(ident.get("updated"), str) else datetime.now(timezone.utc),
        )

    def _save(self, project_path: Path, identity: Identity) -> None:
        identity_path = project_path / self.SDOS_DIR / self.IDENTITY_FILE
        data = {
            "identity": {
                "domain_id": identity.domain_id,
                "name": identity.name,
                "type": identity.type,
                "version": identity.version,
                "state": identity.state,
                "organization": identity.organization,
                "authority": identity.authority,
                "fingerprint": identity.fingerprint,
                "created": identity.created.isoformat(),
                "updated": identity.updated.isoformat(),
            }
        }
        with open(identity_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
