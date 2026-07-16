from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone

from srie.kernel.identity import IdentityService
from srie.kernel.registry import RegistryService
from srie.kernel.manifest import ManifestService
from srie.kernel.lifecycle import Lifecycle, RuntimeState
from srie.sdk.models import Project


class Runtime:
    """Kernel boot coordinator."""

    def __init__(self):
        self.identity = IdentityService()
        self.registry = RegistryService()
        self.manifest_service = ManifestService()
        self.lifecycle = Lifecycle()

    def boot(self, project_path: Path) -> Project:
        self.lifecycle.reset()
        self.lifecycle.transition(RuntimeState.STARTING)

        project = Project(path=project_path)

        project.identity = self.identity.ensure(project_path)
        self.manifest_service.create(project_path)

        project.registry = self.registry.init(project_path)

        manifest = self.manifest_service.load(project_path)
        if manifest:
            manifest.kernel = {
                "identity": project.identity.state,
                "registry": "ready",
            }
            manifest.state = "RUNNING"
            manifest.uptime_seconds = 0
            self.manifest_service.update(project_path, manifest)
            project.manifest = manifest

        self.lifecycle.transition(RuntimeState.RUNNING)
        return project
