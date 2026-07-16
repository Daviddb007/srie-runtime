from __future__ import annotations
from pathlib import Path

from srie.kernel.runtime import Runtime
from srie.kernel.identity import IdentityService
from srie.kernel.manifest import ManifestService
from srie.services.persistence.graph_repository import GraphRepository
from srie.services.persistence.twin_repository import TwinRepository
from srie.services.persistence.report_repository import ReportRepository
from srie.sdk.models import Project, Identity, Manifest, DiscoveryResult, DigitalTwin, IndicatorReport, Graph


class SDK:

    def __init__(self, project_path: str):
        self._path = Path(project_path).resolve()
        self._runtime = Runtime()
        self._identity_service = IdentityService()
        self._manifest_service = ManifestService()
        self._graph_repo = GraphRepository()
        self._twin_repo = TwinRepository()
        self._report_repo = ReportRepository()
        self._project: Project | None = None
        self._last_discovery: DiscoveryResult | None = None

    @property
    def path(self) -> Path:
        return self._path

    def identity(self) -> Identity:
        return self._identity_service.ensure(self._path)

    def init(self) -> Project:
        self._project = self._runtime.boot(self._path)
        return self._project

    def discover(self) -> DiscoveryResult:
        self._ensure_booted()
        import importlib.util
        scanner_path = Path(__file__).parent.parent / "modules" / "discovery" / "scanner.py"
        spec = importlib.util.spec_from_file_location("discovery_scanner", scanner_path)
        if spec and spec.loader:
            disc_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(disc_mod)
            result = disc_mod.scan(self._path)
        else:
            from srie.sdk.models import DiscoveryResult
            result = DiscoveryResult(languages=[], frameworks=[])
            self._last_discovery = result
            return result

        self._last_discovery = result

        if result.graph:
            self._graph_repo.save(self._path, result.graph)

        twin = DigitalTwin(
            project_id=self._project.identity.domain_id if self._project and self._project.identity else "unknown",
            nodes=result.graph.nodes if result.graph else [],
            relationships=result.graph.relationships if result.graph else [],
            version=1,
        )
        self._twin_repo.save(self._path, twin)

        if self._runtime.journal():
            self._runtime.journal().append({
                "type": "DISCOVERY_COMPLETE",
                "source": "module:discovery",
                "message": f"Discovered {len(result.languages)} languages, {len(result.frameworks)} frameworks, {result.files.total if result.files else 0} files",
                "data": {"confidence": result.confidence, "languages": [l.name for l in result.languages]},
            })

        return result

    def indicators(self) -> IndicatorReport:
        twin = self._twin_repo.load(self._path)
        if not twin:
            self.discover()
            twin = self._twin_repo.load(self._path)

        report = IndicatorReport()
        if twin:
            total = len(twin.nodes)
            synced = sum(1 for n in twin.nodes if n.state == "SYNCED")
            report.srie_score = (synced / total * 100) if total > 0 else 0
            report.by_domain = {n.label or n.type: 50.0 for n in twin.nodes}
            report.confidence = 0.7

        if report.srie_score >= 90:
            report.maturity_level = "L5"
        elif report.srie_score >= 70:
            report.maturity_level = "L3"
        elif report.srie_score >= 50:
            report.maturity_level = "L2"
        elif report.srie_score >= 20:
            report.maturity_level = "L1"
        else:
            report.maturity_level = "L0"

        self._report_repo.save(self._path, report)
        if twin:
            twin.indicators = report
            twin.version += 1
            self._twin_repo.save(self._path, twin)

        if self._runtime.journal():
            self._runtime.journal().append({
                "type": "INDICATORS_CALCULATED",
                "source": "module:indicators",
                "message": f"SRIE Score: {report.srie_score:.1f}, Maturity: {report.maturity_level}",
                "data": {"score": report.srie_score, "maturity": report.maturity_level},
            })

        return report

    def twin(self) -> DigitalTwin | None:
        return self._twin_repo.load(self._path)

    def graph(self) -> Graph | None:
        return self._graph_repo.load(self._path)

    def manifest(self) -> Manifest | None:
        return self._manifest_service.load(self._path)

    def operational_age(self) -> dict:
        self._ensure_path()
        return self._runtime.operational_age()

    def pause(self) -> None:
        self._ensure_booted()
        self._runtime.pause()

    def resume(self) -> Project:
        self._project = self._runtime.resume(self._path)
        return self._project

    def checkpoint(self) -> int:
        self._ensure_booted()
        return self._runtime.checkpoint()

    def journal(self, limit: int = 10) -> list[dict]:
        self._ensure_path()
        j = self._runtime.journal()
        if j:
            return j.recent(limit)
        return []

    def cognitive(self) -> dict:
        self._ensure_path()
        c = self._runtime.cognitive()
        if c:
            return c.snapshot()
        return {"hypotheses": {}, "total": 0}

    def intent(self) -> dict:
        self._ensure_path()
        i = self._runtime.intent()
        if i:
            return i.current()
        return {"objective": None}

    def operational_age(self) -> dict:
        self._ensure_path()
        return self._runtime.operational_age()

    def plan(self):
        self._ensure_booted()
        from srie.sdk.models import Plan
        return Plan(objectives=["Improve project maturity"])

    def session_start(self, user: str = "system") -> dict:
        from srie.kernel.session import Session
        s = Session(self._path)
        session = s.start(user=user)
        if self._runtime.journal():
            self._runtime.journal().append({
                "type": "SESSION_STARTED",
                "source": "kernel",
                "message": f"Session {session['id']} started by {user}",
                "data": {"session_id": session["id"], "user": user},
            })
        return session

    def session_end(self) -> dict:
        from srie.kernel.session import Session
        s = Session(self._path)
        session = s.end()
        if self._runtime.journal():
            self._runtime.journal().append({
                "type": "SESSION_ENDED",
                "source": "kernel",
                "message": f"Session {session['id']} ended — {session['duration_seconds']}s",
                "data": {"session_id": session["id"], "duration": session["duration_seconds"]},
            })
        return session

    def session_status(self) -> dict | None:
        from srie.kernel.session import Session
        s = Session(self._path)
        return s.current()

    def work_dna(self) -> dict:
        from srie.services.work_log import WorkLog
        wl = WorkLog(self._path)
        return wl.dna()

    def _ensure_path(self) -> None:
        if not self._runtime.path:
            self._runtime._init_path(self._path)

    def _ensure_booted(self) -> None:
        if not self._project:
            self._project = self._runtime.boot(self._path)
