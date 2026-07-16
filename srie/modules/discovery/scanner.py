from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import subprocess
from collections import defaultdict

from srie.sdk.models import (
    DiscoveryResult, Language, Framework, FileInventory,
    GitState, Dependency, Graph, Node, Relationship
)


LANGUAGE_MAP = {
    ".py": ("Python", {"requirements.txt", "pyproject.toml", "setup.py", "Pipfile"}),
    ".js": ("JavaScript", {"package.json"}),
    ".ts": ("TypeScript", {"tsconfig.json"}),
    ".go": ("Go", {"go.mod"}),
    ".rs": ("Rust", {"Cargo.toml"}),
    ".java": ("Java", {"pom.xml", "build.gradle"}),
    ".rb": ("Ruby", {"Gemfile"}),
    ".php": ("PHP", {"composer.json"}),
    ".cs": ("C#", {".csproj", ".sln"}),
    ".swift": ("Swift", {"Package.swift"}),
    ".html": ("HTML", set()),
    ".css": ("CSS", set()),
}


def scan(project_path: Path) -> DiscoveryResult:
    languages = _detect_languages(project_path)
    frameworks = _detect_frameworks(project_path)
    files = _count_files(project_path)
    git = _detect_git(project_path)
    deps = _detect_dependencies(project_path)
    graph = _build_graph(project_path, languages, frameworks)
    confidence = _calculate_confidence(languages, frameworks, git)

    return DiscoveryResult(
        languages=languages,
        frameworks=frameworks,
        files=files,
        git=git,
        dependencies=deps,
        graph=graph,
        confidence=confidence,
    )


def _detect_languages(project_path: Path) -> list[Language]:
    counts: dict[str, int] = defaultdict(int)
    for f in project_path.rglob("*"):
        if f.is_file() and f.suffix in LANGUAGE_MAP:
            counts[f.suffix] += 1

    languages = []
    for ext, count in counts.items():
        name, _ = LANGUAGE_MAP[ext]
        languages.append(Language(name=name, version="", files=count))

    for f in project_path.iterdir():
        if f.is_file():
            for ext, (name, config_files) in LANGUAGE_MAP.items():
                if f.name in config_files:
                    if not any(l.name == name for l in languages):
                        languages.append(Language(name=name, files=0))

    return languages


def _detect_frameworks(project_path: Path) -> list[Framework]:
    frameworks = []
    detectors = {
        "Flask": ["flask", "requirements.txt", "pyproject.toml"],
        "Django": ["django", "requirements.txt", "pyproject.toml"],
        "FastAPI": ["fastapi", "requirements.txt", "pyproject.toml"],
        "React": ["react", "package.json"],
        "Vue": ["vue", "package.json"],
        "Express": ["express", "package.json"],
    }

    for name, (dep, *files) in detectors.items():
        for fname in files:
            fpath = project_path / fname
            if fpath.exists():
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                if dep in content:
                    frameworks.append(Framework(name=name, confidence=0.8))
                    break

    return frameworks


def _count_files(project_path: Path) -> FileInventory:
    total = 0
    by_ext: dict[str, int] = defaultdict(int)
    by_dir: dict[str, int] = defaultdict(int)

    for f in project_path.rglob("*"):
        if f.is_file():
            total += 1
            by_ext[f.suffix or "(no ext)"] += 1
            parent = f.parent.relative_to(project_path)
            parent_str = str(parent) if str(parent) != "." else "/"
            by_dir[parent_str] += 1

    return FileInventory(total=total, by_extension=dict(by_ext), by_directory=dict(by_dir))


def _detect_git(project_path: Path) -> GitState | None:
    git_dir = project_path / ".git"
    if not git_dir.exists():
        return None

    try:
        current = ""
        try:
            current = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=project_path, capture_output=True, text=True, timeout=5
            ).stdout.strip()
        except Exception:
            pass

        branches_str = ""
        try:
            branches_str = subprocess.run(
                ["git", "branch", "--format=%(refname:short)"],
                cwd=project_path, capture_output=True, text=True, timeout=5
            ).stdout.strip()
        except Exception:
            pass
        branches = [b for b in branches_str.split("\n") if b] if branches_str else []

        last_hash = ""
        last_msg = ""
        last_date = None
        try:
            log = subprocess.run(
                ["git", "log", "-1", "--format=%H|||%s|||%aI"],
                cwd=project_path, capture_output=True, text=True, timeout=5
            ).stdout.strip()
            if log and "|||" in log:
                parts = log.split("|||")
                last_hash = parts[0]
                last_msg = parts[1] if len(parts) > 1 else ""
                if len(parts) > 2:
                    try:
                        last_date = datetime.fromisoformat(parts[2])
                    except Exception:
                        pass
        except Exception:
            pass

        return GitState(
            branches=branches,
            current_branch=current or None,
            last_commit_hash=last_hash or None,
            last_commit_message=last_msg or None,
            last_commit_date=last_date,
        )
    except Exception:
        return None


def _detect_dependencies(project_path: Path) -> list[Dependency]:
    deps = []
    req_file = project_path / "requirements.txt"
    if req_file.exists():
        for line in req_file.read_text(encoding="utf-8", errors="ignore").split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "==" in line:
                parts = line.split("==")
                deps.append(Dependency(name=parts[0].strip(), version=parts[1].strip() if len(parts) > 1 else None))
    return deps


def _build_graph(project_path: Path, languages: list[Language], frameworks: list[Framework]) -> Graph:
    nodes = [
        Node(id="PROJECT", type="raiz", label=project_path.name, state="SYNCED"),
    ]

    if languages:
        nodes.append(Node(id="LANGUAGES", type="dominio", label="Languages", state="SYNCED"))

    if frameworks:
        nodes.append(Node(id="FRAMEWORKS", type="dominio", label="Frameworks", state="SYNCED"))

    src_dir = project_path / "src"
    if src_dir.exists():
        nodes.append(Node(id="SOURCE", type="dominio", label="Source Code", state="SYNCED"))

    test_dir = project_path / "tests"
    if test_dir.exists():
        nodes.append(Node(id="TESTS", type="dominio", label="Tests", state="SYNCED"))

    docs_dir = project_path / "docs"
    if docs_dir.exists():
        nodes.append(Node(id="DOCS", type="dominio", label="Documentation", state="SYNCED"))

    if (project_path / ".git").exists():
        nodes.append(Node(id="VCS", type="dominio", label="Version Control", state="SYNCED"))

    relationships = [
        Relationship(source=nodes[0].id, target=n.id, type="contains", weight=1.0)
        for n in nodes[1:]
    ]

    return Graph(nodes=nodes, relationships=relationships)


def _calculate_confidence(languages: list[Language], frameworks: list[Framework], git: GitState | None) -> float:
    score = 0.0
    if languages:
        score += 0.4
    if frameworks:
        score += 0.3
    if git:
        score += 0.3
    return min(score, 1.0)
