from __future__ import annotations
from pathlib import Path

from srie.kernel.runtime import Runtime
from srie.kernel.identity import IdentityService
from srie.kernel.manifest import ManifestService
from srie.sdk.models import Project, Identity, Manifest


class SDK:

    def __init__(self, project_path: str):
        self._path = Path(project_path).resolve()
        self._runtime = Runtime()
        self._identity_service = IdentityService()
        self._manifest_service = ManifestService()
        self._project: Project | None = None

    @property
    def path(self) -> Path:
        return self._path

    def identity(self) -> Identity:
        return self._identity_service.ensure(self._path)

    def init(self) -> Project:
        self._project = self._runtime.boot(self._path)
        return self._project

    def manifest(self) -> Manifest | None:
        return self._manifest_service.load(self._path)

    def _ensure_booted(self) -> None:
        if not self._project:
            self._project = self._runtime.boot(self._path)
