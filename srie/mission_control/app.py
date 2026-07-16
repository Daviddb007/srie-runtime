from flask import Flask, render_template, jsonify, request

app = Flask(__name__, template_folder="templates")

_SDK_INSTANCE = None


def init_app(sdk):
    global _SDK_INSTANCE
    _SDK_INSTANCE = sdk


@app.route("/")
def index():
    return render_template("mission_control.html", room="universe")


@app.route("/room/<room_name>")
def room(room_name):
    return render_template("mission_control.html", room=room_name)


@app.route("/api/inspect")
def api_inspect():
    sdk = _get_sdk()
    section = request.args.get("section")
    if section:
        from srie.cli.commands.inspect import sections
        func = sections.get(section)
        if func:
            return jsonify(func(sdk))
        return jsonify({"error": f"Unknown section: {section}"}), 404
    from srie.cli.commands.inspect import _build_full_tree
    return jsonify(_build_full_tree(sdk))


@app.route("/api/why")
def api_why():
    sdk = _get_sdk()
    manifest = sdk.manifest()
    age = sdk.operational_age()
    return jsonify({
        "state": age.get("state", "unknown"),
        "born": str(age.get("born", "")),
        "checkpoints": age.get("checkpoints", 0),
        "modules": len(manifest.modules) if manifest else 0,
    })


@app.route("/api/history")
def api_history():
    sdk = _get_sdk()
    limit = request.args.get("limit", 20, type=int)
    events = sdk.journal(limit)
    return jsonify([{
        "timestamp": e.get("timestamp", "")[:19],
        "source": e.get("source", ""),
        "message": e.get("message", ""),
        "type": e.get("type", ""),
    } for e in reversed(events)])


@app.route("/api/universe")
def api_universe():
    sdk = _get_sdk()
    from srie.kernel.universe import Universe
    u = Universe(sdk.path)
    try:
        return jsonify(u.twin())
    except FileNotFoundError:
        return jsonify({"error": "Universe not initialized"}), 404


@app.route("/api/identity")
def api_identity():
    sdk = _get_sdk()
    identity = sdk.identity()
    return jsonify({
        "domain_id": identity.domain_id,
        "name": identity.name,
        "type": identity.type,
        "state": identity.state,
        "fingerprint": identity.fingerprint,
    })


@app.route("/api/runtime")
def api_runtime():
    sdk = _get_sdk()
    manifest = sdk.manifest()
    age = sdk.operational_age()
    return jsonify({
        "state": age.get("state", "unknown"),
        "version": manifest.runtime_version if manifest else "N/A",
        "modules": [{"id": m.id, "version": m.version, "state": m.state} for m in (manifest.modules if manifest else [])],
        "checkpoints": age.get("checkpoints", 0),
    })


@app.route("/api/cognitive")
def api_cognitive():
    sdk = _get_sdk()
    cognitive = sdk.cognitive()
    intent = sdk.intent()
    return jsonify({
        "hypotheses": cognitive,
        "intent": intent,
    })


@app.route("/api/sessions")
def api_sessions():
    sdk = _get_sdk()
    from srie.kernel.session import Session
    s = Session(sdk.path)
    current = s.current()
    all_sessions = s.list_all()
    return jsonify({
        "current": current,
        "total": len(all_sessions),
        "sessions": all_sessions[-10:] if all_sessions else [],
    })


@app.route("/api/dna")
def api_dna():
    sdk = _get_sdk()
    from srie.services.work_log import WorkLog
    wl = WorkLog(sdk.path)
    return jsonify(wl.dna())


@app.route("/api/executions")
def api_executions():
    sdk = _get_sdk()
    from srie.kernel.execution import ExecutionOrchestrator
    o = ExecutionOrchestrator(sdk.path)
    return jsonify({
        "status": o.execution_status(),
        "executions": o.list_executions(),
    })


def _get_sdk():
    if _SDK_INSTANCE:
        return _SDK_INSTANCE
    from srie.sdk.client import SDK
    import os
    project = os.environ.get("SRIE_PROJECT", ".")
    return SDK(project)
