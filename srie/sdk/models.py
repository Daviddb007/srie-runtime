from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import hashlib


@dataclass
class Language:
    name: str
    version: str | None = None
    files: int = 0

@dataclass
class Framework:
    name: str
    version: str | None = None
    confidence: float = 1.0

@dataclass
class FileInventory:
    total: int = 0
    by_extension: dict[str, int] = field(default_factory=dict)
    by_directory: dict[str, int] = field(default_factory=dict)

@dataclass
class GitState:
    branches: list[str] = field(default_factory=list)
    current_branch: str | None = None
    last_commit_hash: str | None = None
    last_commit_message: str | None = None
    last_commit_date: datetime | None = None

@dataclass
class Dependency:
    name: str
    version: str | None = None
    type: str = "python"

@dataclass
class Node:
    id: str
    type: str
    label: str = ""
    state: str = "PENDING"
    metadata: dict = field(default_factory=dict)

@dataclass
class Relationship:
    source: str
    target: str
    type: str
    weight: float = 1.0

@dataclass
class Event:
    source: str
    type: str
    target: str
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Identity:
    domain_id: str
    name: str
    type: str = "standalone"
    version: str = "1.0.0"
    state: str = "ACTIVE"
    organization: dict | None = None
    authority: dict | None = None
    fingerprint: str = ""
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not self.fingerprint:
            raw = f"{self.domain_id}:{self.name}:{self.version}"
            self.fingerprint = f"sha256:{hashlib.sha256(raw.encode()).hexdigest()[:12]}"
        if self.authority is None:
            self.authority = {"nivel": "Domain", "puede_crear_capabilities": True, "puede_modificar_registry": "local"}

@dataclass
class Graph:
    nodes: list[Node]
    relationships: list[Relationship]
    events: list[Event] = field(default_factory=list)
    version: int = 1
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class DiscoveryResult:
    languages: list[Language]
    frameworks: list[Framework]
    files: FileInventory | None = None
    git: GitState | None = None
    dependencies: list[Dependency] | None = None
    graph: Graph | None = None
    confidence: float = 0.0

@dataclass
class IndicatorReport:
    srie_score: float = 0.0
    maturity_level: str = "L0"
    by_domain: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trends: dict | None = None

@dataclass
class DigitalTwin:
    project_id: str
    nodes: list[Node]
    relationships: list[Relationship]
    indicators: IndicatorReport | None = None
    metrics: dict = field(default_factory=dict)
    last_sync: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1

@dataclass
class ModuleInfo:
    id: str
    version: str
    state: str = "IDLE"

@dataclass
class Manifest:
    runtime_version: str
    state: str
    kernel: dict
    modules: list[ModuleInfo]
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    uptime_seconds: int = 0

@dataclass
class Capability:
    id: str
    name: str
    description: str = ""
    effort: str = "medium"
    impact: str = "medium"

@dataclass
class PrioritizedItem:
    capability: Capability
    priority: int = 0
    score: float = 0.0

@dataclass
class Risk:
    description: str
    probability: str = "low"
    impact: str = "low"
    mitigation: str = ""

@dataclass
class Plan:
    objectives: list[str] = field(default_factory=list)
    capabilities: list[Capability] = field(default_factory=list)
    priorities: list[PrioritizedItem] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class Registry:
    entities: dict[str, dict] = field(default_factory=dict)
    domains: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)

@dataclass
class Project:
    path: Path
    identity: Identity | None = None
    graph: Graph | None = None
    twin: DigitalTwin | None = None
    registry: Registry | None = None
    indicators: IndicatorReport | None = None
    manifest: Manifest | None = None
