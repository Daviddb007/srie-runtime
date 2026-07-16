from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone

from srie.kernel.identity import IdentityService
from srie.kernel.registry import RegistryService
from srie.kernel.manifest import ManifestService
from srie.kernel.lifecycle import Lifecycle, RuntimeState
from srie.services.loader.loader import ModuleLoader
from srie.services.persistence.graph_repository import GraphRepository
from srie.services.persistence.twin_repository import TwinRepository
from srie.sdk.models import Project, DigitalTwin


class Runtime:
    """Kernel boot coordinator."""

    def __init__(self, modules_dir: Path | None = None):
        self.identity = IdentityService()
        self.registry = RegistryService()
        self.manifest_service = ManifestService()
        self.lifecycle = Lifecycle()
        self._modules_dir = modules_dir or Path(__file__).parent.parent / "modules"

    def boot(self, project_path: Path) -> Project:
        self.lifecycle.reset()
        self.lifecycle.transition(RuntimeState.STARTING)

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

        self.lifecycle.transition(RuntimeState.RUNNING)
        return project
