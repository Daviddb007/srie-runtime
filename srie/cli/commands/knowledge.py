from srie.services.knowledge import KnowledgeEngine
from srie.services.evolution import EvolutionEngine
from pathlib import Path


def _know(project_path: str) -> KnowledgeEngine:
    return KnowledgeEngine(Path(project_path).resolve())

def _evo(project_path: str) -> EvolutionEngine:
    return EvolutionEngine(Path(project_path).resolve())


# Knowledge
def pattern_extract(project_path: str = ".", pattern_type: str = "success", title: str = "Pattern", description: str = "", source: str = "manual"):
    p = _know(project_path).extract_pattern(pattern_type, title, description, source)
    print(f"Pattern {p['id']} extracted: {title}")

def case_store(project_path: str = ".", action: str = "discover", outcome: str = "success", score: float = 0.9):
    c = _know(project_path).store_case("execution", action, outcome, {"source": "cli"}, score)
    print(f"Case {c['id']} stored: {action} -> {outcome}")

def knowledge_status(project_path: str = "."):
    eng = _know(project_path)
    patterns = eng.list_patterns()
    cases = eng.list_cases()
    reuse = eng.reuse_rate()
    print(f"Knowledge Base:")
    print(f"  Patterns: {len(patterns)}")
    print(f"  Cases: {len(cases)}")
    print(f"  Reuse rate: {reuse}%")
    if patterns:
        print(f"\nRecent patterns:")
        for p in patterns[-5:]:
            print(f"  [{p['type']}] {p['title']} (conf: {p.get('confidence', 0):.2f})")
    if cases:
        print(f"\nRecent cases:")
        for c in cases[-5:]:
            print(f"  {c['action']} -> {c['outcome']} (score: {c.get('score', 0):.2f})")

def suggest_reuse(project_path: str = ".", action: str = "discover"):
    result = _know(project_path).suggest_reuse(action, {"source": "cli"})
    if result:
        print(f"Reuse suggestion for '{action}':")
        print(f"  Based on: {result['based_on']}")
        print(f"  Expected: {result['expected_outcome']}")
        print(f"  Confidence: {result['confidence']}")
    else:
        print(f"No reuse suggestion for '{action}'")


# Evolution
def drift(project_path: str = "."):
    drifts = _evo(project_path).detect_drift()
    print(f"Drift analysis:")
    for d in drifts:
        print(f"  [{d['severity']}] {d['message']}")

def evolve(project_path: str = "."):
    suggestion = _evo(project_path).suggest_evolution()
    print(f"Evolution suggestions ({suggestion['total_suggestions']}):")
    for s in suggestion['suggestions']:
        print(f"  [{s['priority']}] {s['area']}: {s['message']}")
        if s.get('suggested'):
            print(f"    → {s['suggested']}")
    dna = suggestion['dna_summary']
    print(f"\nDNA: {dna['total_sessions']} sessions, {dna['total_hypotheses']} hypotheses, confidence {dna.get('confidence', 0):.2f}")

def auto_evolve(project_path: str = "."):
    result = _evo(project_path).auto_evolve()
    print(f"Auto-evolution applied: {len(result['applied'])} actions")
    print(f"Open suggestions: {len(result['suggestions'])}")
