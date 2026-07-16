from srie.services.sandbox import Sandbox
from srie.services.repair import RepairEngine
from srie.services.deployment import Deployment
from pathlib import Path


def _sand(project_path: str) -> Sandbox:
    return Sandbox(Path(project_path).resolve())

def _rep(project_path: str) -> RepairEngine:
    return RepairEngine(Path(project_path).resolve())

def _dep(project_path: str) -> Deployment:
    return Deployment(Path(project_path).resolve())


# Sandbox
def sandbox_create(project_path: str = ".", name: str = "sandbox-test"):
    env = _sand(project_path).create_environment(name)
    print(f"Sandbox {env['id']} created: {name}")

def sandbox_test(project_path: str = ".", env_id: str = "", test_name: str = "verify-action", action: str = "verify"):
    test = _sand(project_path).run_test(env_id, test_name, action)
    print(f"Test {test['id']}: {test['state']}")
    print(f"  Details: {test.get('details', '')}")

def sandbox_report(project_path: str = ".", env_id: str = ""):
    r = _sand(project_path).report(env_id)
    print(f"Sandbox {r.get('environment', '?')}")
    print(f"  State: {r.get('state', '?')}")
    print(f"  Tests: {r.get('total_tests', 0)} ({r.get('passed', 0)} passed, {r.get('failed', 0)} failed)")
    print(f"  Success rate: {r.get('success_rate', 0):.1f}%")

# Repair
def repair_diagnose(project_path: str = "."):
    issues = _rep(project_path).diagnose()
    if not issues:
        print("No issues detected.")
        return
    print(f"Issues found ({len(issues)}):")
    for i in issues:
        print(f"  [{i['type']}] {i['message']}")
        if i.get('fix'):
            print(f"    Fix: {i['fix']}")

def repair_fix(project_path: str = "."):
    results = _rep(project_path).auto_repair_all()
    if not results:
        print("No issues to fix.")
        return
    print(f"Auto-repair results ({len(results)}):")
    for r in results:
        status = "APPLIED" if r['applied'] else "MANUAL"
        print(f"  [{status}] {r['message']}")

# Deployment
def deploy_target(project_path: str = ".", name: str = "production", environment: str = "production", url: str = ""):
    tgt = _dep(project_path).register_target(name, environment, url)
    print(f"Target {tgt['id']} registered: {name} ({environment})")

def deploy_run(project_path: str = ".", target_id: str = "", version: str = "1.0.0"):
    dep = _dep(project_path).deploy(target_id, version)
    print(f"Deployed v{version} to {target_id}")
    print(f"  Deployment ID: {dep['id']}")

def deploy_rollback(project_path: str = ".", target_id: str = ""):
    result = _dep(project_path).rollback(target_id)
    if "error" in result:
        print(f"Rollback failed: {result['error']}")
    else:
        print(f"Rollback to v{result['version']} completed")

def deploy_status(project_path: str = ".", target_id: str = ""):
    st = _dep(project_path).status(target_id)
    if "error" in st:
        print(f"Error: {st['error']}")
    else:
        print(f"Target: {st.get('target', '?')}")
        print(f"  Environment: {st.get('environment', '?')}")
        print(f"  State: {st.get('state', '?')}")
        print(f"  Deployments: {st.get('total_deployments', 0)}")
