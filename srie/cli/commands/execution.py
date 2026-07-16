from srie.kernel.execution import ExecutionOrchestrator
from pathlib import Path


def _orch(project_path: str) -> ExecutionOrchestrator:
    return ExecutionOrchestrator(Path(project_path).resolve())


def cmd_create(project_path: str = ".", goal: str = "default", priority: str = "medium"):
    exec_data = _orch(project_path).create_execution(goal, priority)
    print(f"Execution {exec_data['id']} created")
    print(f"  Goal: {goal}")
    print(f"  Priority: {priority}")
    print(f"  State: {exec_data['state']}")


def cmd_start(project_path: str = ".", exec_id: str = ""):
    exec_data = _orch(project_path).start_execution(exec_id)
    print(f"Execution {exec_id} started")


def cmd_complete(project_path: str = ".", exec_id: str = ""):
    exec_data = _orch(project_path).complete_execution(exec_id)
    print(f"Execution {exec_id} completed")


def cmd_workflow(project_path: str = ".", exec_id: str = "", name: str = "default"):
    steps = [
        {"name": "Discover", "action": "discover"},
        {"name": "Analyze", "action": "indicators"},
        {"name": "Plan", "action": "plan"},
    ]
    wf = _orch(project_path).add_workflow(exec_id, name, steps)
    print(f"Workflow {wf['id']} added to execution {exec_id}")
    print(f"  Steps: {len(wf['steps'])}")


def cmd_status(project_path: str = "."):
    status = _orch(project_path).execution_status()
    print(f"Executions: {status['total']} total")
    print(f"  Running: {status['running']}")
    print(f"  Pending: {status['pending']}")
    print(f"  Completed: {status['completed']}")
    print(f"  Blocked: {status['blocked']}")
    if status['active']:
        print(f"\nActive executions:")
        for e in _orch(project_path).list_executions():
            if e['state'] in ('RUNNING', 'PENDING'):
                print(f"  {e['id']}: {e['goal'][:50]} [{e['state']}] {e.get('progress', 0)}%")


def cmd_list(project_path: str = "."):
    execs = _orch(project_path).list_executions()
    if not execs:
        print("No executions found.")
        return
    print(f"Executions ({len(execs)}):")
    for e in execs:
        print(f"  {e['id']}: {e['goal'][:50]}")
        print(f"    State: {e['state']} | Progress: {e.get('progress', 0)}% | Priority: {e.get('priority', 'medium')}")
