from srie.sdk.client import SDK


def cmd(
    project_path: str = ".",
    verbose: bool = False,
):
    sdk = SDK(project_path)
    identity = sdk.identity()

    print(f"Domain ID: {identity.domain_id}")
    print(f"Name: {identity.name}")
    print(f"Type: {identity.type}")
    print(f"Version: {identity.version}")
    print(f"State: {identity.state}")
    print(f"Fingerprint: {identity.fingerprint}")
