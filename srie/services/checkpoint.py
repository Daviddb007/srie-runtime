from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json
import tarfile
import io
import hashlib


class Checkpoint:

    def __init__(self, project_path: Path):
        self._cp_dir = project_path / "SDOS" / "checkpoints"
        self._cp_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._cp_dir / "INDEX.yaml"

    def create(self, snapshot_data: dict) -> int:
        cp_id = self._next_id()
        cp_data = {
            "checkpoint_id": cp_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": snapshot_data,
        }

        cp_bytes = json.dumps(cp_data, indent=2, default=str).encode("utf-8")
        cp_hash = hashlib.sha256(cp_bytes).hexdigest()[:16]

        cp_path = self._cp_dir / f"cp-{cp_id:04d}.json"
        with open(cp_path, "w", encoding="utf-8") as f:
            json.dump(cp_data, f, indent=2, default=str)

        self._update_index(cp_id, cp_hash)
        return cp_id

    def latest(self) -> dict | None:
        index = self._load_index()
        if not index:
            return None
        latest_id = max(c["id"] for c in index)
        return self.load(latest_id)

    def load(self, cp_id: int) -> dict | None:
        cp_path = self._cp_dir / f"cp-{cp_id:04d}.json"
        if not cp_path.exists():
            return None
        with open(cp_path, encoding="utf-8") as f:
            return json.load(f)

    def list_all(self) -> list[dict]:
        return self._load_index()

    def _next_id(self) -> int:
        index = self._load_index()
        if not index:
            return 1
        return max(c["id"] for c in index) + 1

    def _load_index(self) -> list[dict]:
        index_path = self._cp_dir / "INDEX.yaml"
        if not index_path.exists():
            return []
        import yaml
        with open(index_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("checkpoints", [])

    def _update_index(self, cp_id: int, cp_hash: str) -> None:
        import yaml
        index = self._load_index()
        index.append({
            "id": cp_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hash": cp_hash,
        })
        with open(self._index_path, "w", encoding="utf-8") as f:
            yaml.dump({"checkpoints": index}, f, default_flow_style=False, allow_unicode=True)
