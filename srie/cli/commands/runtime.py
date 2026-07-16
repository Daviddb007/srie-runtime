from srie.sdk.client import SDK


def cmd(
    project_path: str = ".",
):
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


def modules_cmd(project_path: str = "."):
    from srie.services.loader.resolver import ModuleResolver
    from pathlib import Path

    modules_dir = Path(__file__).parent.parent.parent / "modules"
    resolver = ModuleResolver()
    discovered = resolver.discover(modules_dir)

    if not discovered:
        print("No modules found.")
        return

    print(f"Discovered {len(discovered)} modules:")
    for mod in discovered:
        deps = ", ".join(mod.get("depends_on", []) or [])
        print(f"  - {mod['id']} v{mod.get('version', '?')} [depends: {deps or 'none'}]")


def lock_cmd(project_path: str = "."):
    sdk = SDK(project_path)
    manifest = sdk.manifest()
    if manifest:
        print(f"Runtime Lock — {manifest.state}")
        print(f"  Created: {manifest.created.isoformat()}")
        print(f"  Updated: {manifest.updated.isoformat()}")
    else:
        print("No runtime.lock found.")
