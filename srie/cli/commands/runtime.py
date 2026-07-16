from srie.sdk.client import SDK


def cmd(project_path: str = "."):
    sdk = SDK(project_path)
    manifest = sdk.manifest()
    if manifest:
        print(f"Runtime state: {manifest.state}")
        print(f"Version: {manifest.runtime_version}")
        print(f"Kernel: {manifest.kernel}")
        print(f"Modules: {len(manifest.modules)} loaded")
        for mod in manifest.modules:
            print(f"  - {mod.id} v{mod.version} [{mod.state}]")
    else:
        print("Runtime not initialized. Run 'srie init' first.")


def cmd_pause(project_path: str = "."):
    sdk = SDK(project_path)
    sdk.pause()
    print(f"Runtime paused. State: SUSPENDED")


def cmd_resume(project_path: str = "."):
    sdk = SDK(project_path)
    sdk.resume()
    print(f"Runtime resumed. State: RUNNING")


def cmd_checkpoint(project_path: str = "."):
    sdk = SDK(project_path)
    cp_id = sdk.checkpoint()
    print(f"Checkpoint #{cp_id} created")


def cmd_journal(project_path: str = ".", limit: int = 10):
    sdk = SDK(project_path)
    events = sdk.journal(limit)
    if not events:
        print("No journal entries found.")
        return
    print(f"Recent journal entries ({len(events)}):")
    for evt in events:
        ts = evt.get("timestamp", "?")[:19]
        source = evt.get("source", "?")
        msg = evt.get("message", evt.get("type", "?"))
        print(f"  [{ts}] {source}: {msg}")


def cmd_age(project_path: str = "."):
    sdk = SDK(project_path)
    age = sdk.operational_age()
    print(f"Operational Age:")
    print(f"  Born: {age.get('born', 'N/A')}")
    print(f"  State: {age.get('state', 'N/A')}")
    print(f"  Uptime: {age.get('uptime_seconds', 0)}s")
    print(f"  Checkpoints: {age.get('checkpoints', 0)}")
    print(f"  Hypotheses: {age.get('hypotheses', 0)} ({age.get('hypotheses_validated', 0)} validated)")
