from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone

from srie.kernel.identity import IdentityService
from srie.kernel.registry import RegistryService
from srie.kernel.manifest import ManifestService
from srie.kernel.lifecycle import Lifecycle, RuntimeState
from srie.kernel.cognitive import CognitiveState
from srie.kernel.intent import IntentState
from srie.services.loader.loader import ModuleLoader
from srie.services.persistence.graph_repository import GraphRepository
from srie.services.persistence.twin_repository import TwinRepository
from srie.services.journal import Journal
from srie.services.checkpoint import Checkpoint
from srie.sdk.models import Project, DigitalTwin, ModuleInfo


class Runtime:

    def __init__(self, modules_dir: Path | None = None):
        self.identity = IdentityService()
        self.registry = RegistryService()
        self.manifest_service = ManifestService()
        self.lifecycle = Lifecycle()
        self._modules_dir = modules_dir or Path(__file__).parent.parent / "modules"
        self._path: Path | None = None
        self._journal: Journal | None = None
        self._cognitive: CognitiveState | None = None
        self._intent: IntentState | None = None
        self._checkpoint: Checkpoint | None = None

    @property
    def path(self) -> Path | None:
        return self._path

    def boot(self, project_path: Path) -> Project:
        self.lifecycle.reset()
        self.lifecycle.transition(RuntimeState.STARTING)

        self._path = project_path
        self._journal = Journal(project_path)
        self._cognitive = CognitiveState(project_path)
        self._intent = IntentState(project_path)
        self._checkpoint = Checkpoint(project_path)

        project = Project(path=project_path)

        project.identity = self.identity.ensure(project_path)
        self.manifest_service.create(project_path)

        project.registry = self.registry.init(project_path)

        self.registry.register_entity(project_path, "identity", {"version": "1.0.0", "state": project.identity.state})
        self.registry.register_entity(project_path, "registry", {"version": "1.0.0", "state": "ready"})

        loader = ModuleLoader(project_path)
        loaded_modules = loader.load_all(self._modules_dir)
        project.modules = loaded_modules

        manifest = self.manifest_service.load(project_path)
        if manifest:
            manifest.kernel = {
                "identity": project.identity.state,
                "registry": "ready",
            }
            manifest.modules = loaded_modules
            manifest.state = "RUNNING"
            manifest.uptime_seconds = 0
            self.manifest_service.update(project_path, manifest)
            project.manifest = manifest

        self._journal.append({
            "type": "RUNTIME_BOOTED",
            "source": "kernel",
            "message": f"Runtime booted for {project_path.name} — {len(loaded_modules)} modules loaded",
            "data": {"identity": project.identity.domain_id, "modules": [m.id for m in loaded_modules]},
        })

        self.lifecycle.transition(RuntimeState.RUNNING)
        return project

    def pause(self) -> None:
        if not self._path:
            raise RuntimeError("Runtime not booted")
        self.lifecycle.transition(RuntimeState.SUSPENDED)

        snapshot = self._collect_snapshot()
        cp_id = self._checkpoint.create(snapshot)

        manifest = self.manifest_service.load(self._path)
        if manifest:
            manifest.state = "SUSPENDED"
            manifest.uptime_seconds = self._compute_uptime()
            self.manifest_service.update(self._path, manifest)

        self._journal.append({
            "type": "RUNTIME_PAUSED",
            "source": "kernel",
            "message": f"Runtime paused — checkpoint #{cp_id} created",
            "data": {"checkpoint_id": cp_id},
        })

    def resume(self, project_path: Path | None = None) -> Project:
        if project_path:
            self._init_path(project_path)
        if not self._path:
            raise RuntimeError("Runtime not booted. Call boot() or init() first.")
        self.lifecycle.reset()
        self.lifecycle.transition(RuntimeState.STARTING)

        checkpoint = self._checkpoint.latest()
        if checkpoint:
            data = checkpoint.get("data", {})
            if self._cognitive:
                self._cognitive.restore(data.get("cognitive", {}))
            if self._intent:
                self._intent.restore(data.get("intent", {}))

        manifest = self.manifest_service.load(self._path)
        if manifest:
            manifest.state = "RUNNING"
            self.manifest_service.update(self._path, manifest)

        self._journal.append({
            "type": "RUNTIME_RESUMED",
            "source": "kernel",
            "message": "Runtime resumed from checkpoint",
        })

        self.lifecycle.transition(RuntimeState.RUNNING)
        return self._build_project()

    def checkpoint(self) -> int:
        if not self._path:
            raise RuntimeError("Runtime not booted")
        snapshot = self._collect_snapshot()
        cp_id = self._checkpoint.create(snapshot)
        self._journal.append({
            "type": "CHECKPOINT_CREATED",
            "source": "kernel",
            "message": f"Checkpoint #{cp_id} created",
        })
        return cp_id

    def journal(self) -> Journal:
        if not self._journal:
            raise RuntimeError("Journal not initialized")
        return self._journal

    def cognitive(self) -> CognitiveState:
        if not self._cognitive:
            raise RuntimeError("Cognitive state not initialized")
        return self._cognitive

    def intent(self) -> IntentState:
        if not self._intent:
            raise RuntimeError("Intent state not initialized")
        return self._intent

    def operational_age(self) -> dict:
        if not self._path:
            return {"born": None, "uptime_seconds": 0}
        manifest = self.manifest_service.load(self._path)
        cognitive_snap = self._cognitive.snapshot() if self._cognitive else {}
        return {
            "born": manifest.created.isoformat() if manifest else None,
            "uptime_seconds": self._compute_uptime(),
            "state": manifest.state if manifest else "UNKNOWN",
            "sessions": 0,
            "checkpoints": len(self._checkpoint.list_all()) if self._checkpoint else 0,
            "hypotheses": cognitive_snap.get("total", 0),
            "hypotheses_validated": cognitive_snap.get("validated", 0),
        }

    def _init_path(self, project_path: Path) -> None:
        self._path = project_path
        self._journal = Journal(project_path)
        self._cognitive = CognitiveState(project_path)
        self._intent = IntentState(project_path)
        self._checkpoint = Checkpoint(project_path)

    def _collect_snapshot(self) -> dict:
        return {
            "cognitive": self._cognitive.snapshot() if self._cognitive else {},
            "intent": self._intent.snapshot() if self._intent else {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _compute_uptime(self) -> int:
        return 0

    def _build_project(self) -> Project:
        project = Project(path=self._path)
        project.identity = self.identity.ensure(self._path)
        project.registry = self.registry.init(self._path)
        return project
