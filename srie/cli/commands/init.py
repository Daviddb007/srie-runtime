from srie.sdk.client import SDK
from pathlib import Path


def cmd(
    project_path: str = ".",
    verbose: bool = False,
):
    sdk = SDK(project_path)
    project = sdk.init()

    print(f"SRIE initialized at {Path(project_path).resolve()}")
    print(f"  Domain: {project.identity.domain_id}")
    print(f"  Name: {project.identity.name}")
    print(f"  State: {project.manifest.state if project.manifest else 'unknown'}")

    if verbose:
        print(f"\nIdentity:")
        print(f"  ID: {project.identity.domain_id}")
        print(f"  Fingerprint: {project.identity.fingerprint}")
