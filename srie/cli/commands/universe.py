from srie.kernel.universe import Universe
from pathlib import Path


def cmd_init(project_path: str = ".", name: str = "default"):
    u = Universe(Path(project_path).resolve())
    data = u.ensure(name=name)
    print(f"Universe '{name}' initialized ({data['universe']['id']})")


def cmd_status(project_path: str = "."):
    u = Universe(Path(project_path).resolve())
    try:
        data = u.load()
    except FileNotFoundError:
        print("Universe not initialized. Run 'srie universe init' first.")
        return
    uni = data.get("universe", {})
    print(f"Universe: {uni.get('name', '?')} ({uni.get('id', '?')})")
    print(f"  State: {uni.get('state', '?')}")
    print(f"  Organizations: {len(uni.get('organizations', []))}")
    print(f"  Workspaces: {len(uni.get('workspaces', []))}")
    print(f"  Projects: {len(uni.get('projects', []))}")
    print(f"  Domains: {len(uni.get('domains', []))}")


def cmd_org_add(project_path: str = ".", name: str = "default"):
    u = Universe(Path(project_path).resolve())
    u.ensure("default")
    org = u.register_organization(name)
    print(f"Organization '{name}' registered ({org['id']})")


def cmd_ws_add(project_path: str = ".", name: str = "default", org: str | None = None):
    u = Universe(Path(project_path).resolve())
    u.ensure("default")
    ws = u.register_workspace(name, org)
    print(f"Workspace '{name}' registered ({ws['id']})")


def cmd_project_add(project_path: str = ".", name: str = "default", workspace: str | None = None):
    u = Universe(Path(project_path).resolve())
    u.ensure("default")
    proj = u.register_project(name, workspace)
    print(f"Project '{name}' registered ({proj['id']})")


def cmd_chain(project_path: str = ".", entity_id: str = ""):
    u = Universe(Path(project_path).resolve())
    chain = u.ownership_chain(entity_id)
    print("Ownership Chain:")
    for entry in chain:
        print(f"  {entry['level']:15s} {entry['id']:20s} {entry['name']}")


def cmd_twin(project_path: str = "."):
    u = Universe(Path(project_path).resolve())
    twin = u.twin()
    print("Universe Digital Twin:")
    print(f"  Organizations: {twin['total_organizations']}")
    print(f"  Workspaces: {twin['total_workspaces']}")
    print(f"  Projects: {twin['total_projects']}")
    print(f"  Domains: {twin['total_domains']}")
    print(f"  State: {twin['state']}")
