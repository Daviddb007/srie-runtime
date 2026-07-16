from srie.sdk.client import SDK


def cmd(
    project_path: str = ".",
    verbose: bool = False,
):
    sdk = SDK(project_path)
    result = sdk.discover()

    print(f"Discovery complete (confidence: {result.confidence:.2f})")
    print(f"\nLanguages:")
    for lang in result.languages:
        print(f"  - {lang.name} ({lang.files} files)")

    print(f"\nFrameworks:")
    for fw in result.frameworks:
        print(f"  - {fw.name} (confidence: {fw.confidence:.2f})")

    print(f"\nFiles: {result.files.total if result.files else 0}")

    if result.git:
        print(f"\nGit: {result.git.current_branch or 'detected'}")
        if result.git.last_commit_message:
            print(f"  Last commit: {result.git.last_commit_message[:60]}")

    if verbose and result.graph:
        print(f"\nGraph: {len(result.graph.nodes)} nodes, {len(result.graph.relationships)} relationships")
