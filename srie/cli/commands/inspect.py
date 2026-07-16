from srie.sdk.client import SDK
from pathlib import Path


def cmd_inspect(project_path: str = ".", section: str | None = None):
    sdk = SDK(project_path)

    sections = {
        "identity": _inspect_identity,
        "runtime": _inspect_runtime,
        "universe": _inspect_universe,
        "cognitive": _inspect_cognitive,
        "tasks": _inspect_tasks,
        "modules": _inspect_modules,
        "workspace": _inspect_workspace,
        "health": _inspect_health,
    }

    if section:
        func = sections.get(section)
        if func:
            tree = func(sdk)
            _print_tree(tree)
        else:
            print(f"Unknown section: {section}")
            print(f"Available: {', '.join(sections.keys())}")
    else:
        tree = _build_full_tree(sdk)
        _print_tree(tree)


def cmd_why(project_path: str = "."):
    sdk = SDK(project_path)
    manifest = sdk.manifest()

    print("Runtime Status Analysis")
    print("=" * 60)

    if manifest:
        state = manifest.state
        if state == "FAILED":
            print("  Why is the Runtime FAILED?")
            print("  -> Check runtime.lock for error details")
            print("  -> Run 'srie runtime status' for module states")
        elif state == "SUSPENDED":
            print("  Why is the Runtime SUSPENDED?")
            print("  -> It was paused. Run 'srie runtime resume' to continue.")
        elif state == "RUNNING":
            _print_why_running(sdk)
    else:
        print("  Runtime not initialized. Run 'srie init' first.")


def cmd_explain(project_path: str = ".", topic: str = "system"):
    sdk = SDK(project_path)

    if topic.startswith("hypothesis"):
        parts = topic.split()
        hid = parts[1] if len(parts) > 1 else None
        _explain_hypothesis(sdk, hid)
    elif topic == "score":
        _explain_score(sdk)
    elif topic == "decision":
        _explain_last_decision(sdk)
    else:
        _explain_system(sdk)


def cmd_history(project_path: str = ".", limit: int = 20):
    sdk = SDK(project_path)
    events = sdk.journal(limit)

    if not events:
        print("No history available.")
        return

    print(f"History (last {len(events)} events):")
    print("=" * 60)
    for evt in reversed(events):
        ts = evt.get("timestamp", "?")[:19]
        source = evt.get("source", "?")
        msg = evt.get("message", evt.get("type", "?"))
        print(f"  [{ts}] {source}: {msg}")


def _build_full_tree(sdk: SDK) -> dict:
    return {
        "label": f"SRIE Runtime @ {sdk.path.name}",
        "children": [
            _inspect_identity(sdk),
            _inspect_runtime(sdk),
            _inspect_universe(sdk),
            _inspect_workspace(sdk),
            _inspect_cognitive(sdk),
            _inspect_tasks(sdk),
            _inspect_modules(sdk),
            _inspect_health(sdk),
        ]
    }


def _inspect_identity(sdk: SDK) -> dict:
    identity = sdk.identity()
    return {
        "label": "Identity",
        "children": [
            {"label": f"Domain: {identity.domain_id}", "value": identity.domain_id},
            {"label": f"Name: {identity.name}"},
            {"label": f"Type: {identity.type}"},
            {"label": f"State: {identity.state}"},
            {"label": f"Fingerprint: {identity.fingerprint[:20]}..."},
            {"label": f"Created: {identity.created.isoformat()[:19]}"},
        ]
    }


def _inspect_runtime(sdk: SDK) -> dict:
    manifest = sdk.manifest()
    age = sdk.operational_age()
    children = [
        {"label": f"State: {age.get('state', 'N/A')}"},
        {"label": f"Version: {manifest.runtime_version if manifest else 'N/A'}"},
        {"label": f"Born: {str(age.get('born', 'N/A'))[:19]}"},
    ]
    if manifest:
        children.append({"label": f"Uptime: {manifest.uptime_seconds}s"})
        children.append({"label": f"Modules: {len(manifest.modules)} loaded"})
        for mod in manifest.modules:
            children.append({"label": f"  {mod.id}", "value": mod.state})
    children.append({"label": f"Checkpoints: {age.get('checkpoints', 0)}"})
    return {"label": "Runtime", "children": children}


def _inspect_cognitive(sdk: SDK) -> dict:
    cognitive = sdk.cognitive()
    intent = sdk.intent()
    children = [
        {"label": f"Hypotheses: {cognitive.get('total', 0)} ({cognitive.get('active', 0)} active, {cognitive.get('validated', 0)} validated)"},
        {"label": f"Intent: {intent.get('objective', 'none')}"},
        {"label": f"Priority: {intent.get('priority', 'none')}"},
        {"label": f"Milestone: {intent.get('milestone', 'none')}"},
    ]
    active = cognitive.get('hypotheses', {})
    for hid, h in list(active.items())[:5]:
        children.append({"label": f"  [{h.get('status', '?')}] {hid}: {h.get('description', '')[:40]}", "value": f"confidence={h.get('confidence', 0):.2f}"})
    return {"label": "Cognitive", "children": children}


def _inspect_tasks(sdk: SDK) -> dict:
    from srie.kernel.task import Task
    t = Task(sdk.path)
    if not t._base.exists():
        return {"label": "Tasks", "children": [{"label": "No tasks"}]}
    tasks = list(t._base.glob("task-*.yaml"))
    if not tasks:
        return {"label": "Tasks", "children": [{"label": "No tasks"}]}

    states: dict[str, int] = {}
    import yaml
    for tp in tasks:
        with open(tp, encoding="utf-8") as f:
            task = yaml.safe_load(f)
        state = task.get("state", "UNKNOWN")
        states[state] = states.get(state, 0) + 1

    children = [{"label": f"Total: {len(tasks)}"}]
    for state, count in sorted(states.items()):
        children.append({"label": f"  {state}: {count}"})
    return {"label": "Tasks", "children": children}


def _inspect_modules(sdk: SDK) -> dict:
    manifest = sdk.manifest()
    if not manifest:
        return {"label": "Modules", "children": [{"label": "No modules loaded"}]}
    children = []
    for mod in manifest.modules:
        children.append({"label": f"{mod.id} v{mod.version}", "value": mod.state})
    return {"label": "Modules", "children": children}


def _inspect_universe(sdk: SDK) -> dict:
    from srie.kernel.universe import Universe
    u = Universe(sdk.path)
    try:
        twin = u.twin()
    except FileNotFoundError:
        return {"label": "Universe", "children": [{"label": "Not initialized (run: srie universe init)"}]}
    children = [
        {"label": f"Orgs: {twin['total_organizations']}"},
        {"label": f"Workspaces: {twin['total_workspaces']}"},
        {"label": f"Projects: {twin['total_projects']}"},
        {"label": f"Domains: {twin['total_domains']}"},
        {"label": f"State: {twin['state']}"},
    ]
    return {"label": "Universe", "children": children}

def _inspect_workspace(sdk: SDK) -> dict:
    from srie.kernel.workspace import Workspace
    w = Workspace(sdk.path)
    try:
        data = w.load()
    except FileNotFoundError:
        return {"label": "Workspace", "children": [{"label": "Not initialized"}]}
    ws = data.get("workspace", {})
    children = [
        {"label": f"Name: {ws.get('name', 'unknown')}"},
        {"label": f"Org: {ws.get('organization', 'none')}"},
        {"label": f"State: {ws.get('state', 'unknown')}"},
    ]
    return {"label": "Workspace", "children": children}


def _inspect_health(sdk: SDK) -> dict:
    manifest = sdk.manifest()
    import yaml
    health = "OK"
    details = []

    if not manifest:
        health = "UNINITIALIZED"
    elif manifest.state == "FAILED":
        health = "CRITICAL"
    elif manifest.state == "DEGRADED":
        health = "DEGRADED"

    for mod in (manifest.modules if manifest else []):
        if mod.state == "ERROR":
            details.append(f"Module {mod.id} in ERROR")

    return {
        "label": f"Health: {health}",
        "children": [{"label": d} for d in details] or [{"label": "All systems operational"}],
    }


def _print_why_running(sdk: SDK):
    manifest = sdk.manifest()
    print("  Why is the Runtime RUNNING?")
    print("  -> All systems operational")
    if manifest and manifest.modules:
        errors = [m for m in manifest.modules if m.state == "ERROR"]
        if errors:
            print(f"  -> Warning: {len(errors)} module(s) in ERROR state")
    print(f"  -> Last checkpoint: {sdk.operational_age().get('checkpoints', 0)} total")


def _explain_hypothesis(sdk: SDK, hid: str | None):
    cognitive = sdk.cognitive()
    hyps = cognitive.get("hypotheses", {})
    if hid:
        h = hyps.get(hid)
        if h:
            print(f"Hypothesis {hid}")
            print(f"  Description: {h.get('description', 'N/A')}")
            print(f"  Status: {h.get('status', 'N/A')}")
            print(f"  Confidence: {h.get('confidence', 0):.2f}")
            print(f"  Evidence: {h.get('evidence_count', 0)} items")
            print(f"  Created: {h.get('created', 'N/A')}")
            print(f"  Updated: {h.get('updated', 'N/A')}")
        else:
            print(f"Hypothesis {hid} not found")
    else:
        print(f"Total hypotheses: {cognitive.get('total', 0)}")
        print(f"  Active: {cognitive.get('active', 0)}")
        print(f"  Validated: {cognitive.get('validated', 0)}")
        print(f"  Archived: {cognitive.get('archived', 0)}")
        print(f"\nUse: srie explain hypothesis <id>")


def _explain_score(sdk: SDK):
    twin = sdk.twin()
    if twin:
        print(f"Project: {twin.project_id}")
        print(f"Twin version: {twin.version}")
        print(f"Nodes: {len(twin.nodes)}")
        if twin.indicators:
            ind = twin.indicators
            print(f"\nSRIE Score: {ind.srie_score:.1f}")
            print(f"Maturity: {ind.maturity_level}")
            print(f"Confidence: {ind.confidence:.2f}")
    else:
        print("No Digital Twin available. Run 'srie discover' first.")


def _explain_last_decision(sdk: SDK):
    events = sdk.journal(5)
    if events:
        last = events[-1]
        print(f"Last decision: {last.get('type', 'unknown')}")
        print(f"  Source: {last.get('source', 'unknown')}")
        print(f"  Message: {last.get('message', '')}")
        print(f"  Time: {last.get('timestamp', '')[:19]}")
    else:
        print("No decisions recorded yet.")


def _explain_system(sdk: SDK):
    print("SRIE System Overview")
    print("=" * 60)
    manifest = sdk.manifest()
    age = sdk.operational_age()
    print(f"  State: {age.get('state', 'N/A')}")
    print(f"  Born: {str(age.get('born', 'N/A'))[:19]}")
    print(f"  Version: {manifest.runtime_version if manifest else 'N/A'}")
    print(f"  Modules: {len(manifest.modules) if manifest else 0}")
    print(f"  Checkpoints: {age.get('checkpoints', 0)}")
    print(f"\nUse: srie inspect [section]")
    print(f"     srie why")
    print(f"     srie explain hypothesis <id>")
    print(f"     srie explain score")
    print(f"     srie history")


def _print_tree(node: dict, indent: str = "", is_last: bool = True) -> None:
    label = node.get("label", "")
    value = node.get("value", "")
    prefix = "└── " if is_last else "├── "
    connector = "    " if is_last else "│   "

    if value:
        print(f"{indent}{prefix}{label} [{value}]")
    else:
        print(f"{indent}{prefix}{label}")

    children = node.get("children", [])
    for i, child in enumerate(children):
        is_last_child = i == len(children) - 1
        _print_tree(child, indent + connector, is_last_child)
