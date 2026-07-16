from srie.compiler.pdl import PDLProcessor
from pathlib import Path


def _proc(project_path: str) -> PDLProcessor:
    return PDLProcessor(Path(project_path).resolve())


def cmd_validate(project_path: str = ".", pdl_file: str = ""):
    proc = _proc(project_path)
    try:
        definition = proc.load(Path(pdl_file))
        errors = proc.validate(definition)
        if errors:
            print(f"PDL validation FAILED ({len(errors)} errors):")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"PDL is valid: {definition.get('id', 'unnamed')}")
            print(f"  Goal: {definition.get('goal', 'N/A')}")
            print(f"  Workflows: {len(definition.get('workflows', []))}")
    except Exception as e:
        print(f"Error: {e}")


def cmd_run(project_path: str = ".", pdl_file: str = ""):
    proc = _proc(project_path)
    try:
        definition = proc.load(Path(pdl_file))
        result = proc.execute(definition)
        print(f"Execution started:")
        print(f"  PDL ID: {result['pdl_id']}")
        print(f"  Execution ID: {result['execution_id']}")
        print(f"  Goal: {result['goal']}")
        print(f"  Workflows: {result['workflows']}")
        print(f"  State: {result['state']}")
        print(f"\nTrack with: srie exec status {project_path}")
        print(f"Inspect with: srie exec list {project_path}")
    except Exception as e:
        print(f"Error: {e}")


def cmd_template(project_path: str = ".", name: str = "my-process"):
    proc = _proc(project_path)
    template = proc.generate_template(name)
    path = proc.save(template)
    print(f"PDL template saved to: {path}")
    print(f"Edit it and run: srie pdl run {project_path} --file {path}")


def cmd_list(project_path: str = "."):
    proc = _proc(project_path)
    defs = proc.list_definitions()
    if not defs:
        print("No PDL definitions found.")
        return
    print(f"PDL definitions ({len(defs)}):")
    for d in defs:
        print(f"  {d.get('id', '?')}: {d.get('goal', '')[:50]}")
        print(f"    Workflows: {len(d.get('workflows', []))}")
