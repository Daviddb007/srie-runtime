import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import typer
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("srie-runtime")
except PackageNotFoundError:
    __version__ = "0.1.0-dev"

app = typer.Typer(
    name="srie",
    help="SRIE Runtime — Project initialization, discovery, and analysis",
)

def version_callback(value: bool):
    if value:
        typer.echo(f"srie-runtime v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(False, "--version", "-V", help="Show version", callback=version_callback, is_eager=True),
):
    pass

from srie.cli.commands import init as init_cmd
from srie.cli.commands import identity as identity_cmd
from srie.cli.commands import discover as discover_cmd
from srie.cli.commands import indicators as indicators_cmd
from srie.cli.commands import runtime as runtime_cmd
from srie.cli.commands import inspect as inspect_cmd
from srie.cli.commands import universe as universe_cmd
from srie.cli.commands import studio as studio_cmd

@app.command()
def doctor():
    """Check if SRIE Runtime is properly installed."""
    typer.echo(f"[OK] srie-runtime v{__version__}")
    typer.echo("[OK] CLI registered")
    typer.echo("[OK] Kernel package found")
    typer.echo("[OK] SDK package found")

    try:
        import yaml
        typer.echo(f"[OK] PyYAML {yaml.__version__}")
    except ImportError:
        typer.echo("[FAIL] PyYAML not installed")

    typer.echo("\nSRIE Runtime is ready.")

@app.command()
def identity(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Show or create project identity."""
    identity_cmd.cmd(project_path)

@app.command()
def init(
    project_path: str = typer.Argument(".", help="Path to the project"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Initialize SRIE in a project directory."""
    init_cmd.cmd(project_path, verbose)

@app.command()
def discover(
    project_path: str = typer.Argument(".", help="Path to the project"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Discover project structure and technologies."""
    discover_cmd.cmd(project_path, verbose)

@app.command()
def indicators(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Calculate project maturity indicators."""
    indicators_cmd.cmd(project_path)

runtime_typer = typer.Typer(name="runtime", help="Runtime management commands")
app.add_typer(runtime_typer)

@runtime_typer.command()
def status(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Show runtime status."""
    runtime_cmd.cmd(project_path)

@runtime_typer.command()
def pause(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Pause runtime and create checkpoint."""
    runtime_cmd.cmd_pause(project_path)

@runtime_typer.command()
def resume(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Resume runtime from last checkpoint."""
    runtime_cmd.cmd_resume(project_path)

@runtime_typer.command()
def checkpoint(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Create a runtime checkpoint."""
    runtime_cmd.cmd_checkpoint(project_path)

@runtime_typer.command()
def journal(
    project_path: str = typer.Argument(".", help="Path to the project"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of entries"),
):
    """Show recent journal entries."""
    runtime_cmd.cmd_journal(project_path, limit)

@runtime_typer.command()
def age(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Show operational age of the runtime."""
    runtime_cmd.cmd_age(project_path)

@runtime_typer.command()
def session_start(
    project_path: str = typer.Argument(".", help="Path to the project"),
    user: str = typer.Option("system", "--user", "-u", help="User name"),
):
    """Start a new work session."""
    runtime_cmd.cmd_session_start(project_path, user)

@runtime_typer.command()
def session_end(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """End the current work session."""
    runtime_cmd.cmd_session_end(project_path)

@runtime_typer.command()
def session_status(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Show current or last session."""
    runtime_cmd.cmd_session_status(project_path)

@runtime_typer.command()
def dna(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Show work DNA (aggregated session patterns)."""
    runtime_cmd.cmd_dna(project_path)


@app.command()
def inspect(
    project_path: str = typer.Argument(".", help="Path to the project"),
    section: str = typer.Argument(None, help="Section: identity, runtime, cognitive, tasks, modules, workspace, health"),
):
    """Inspect SRIE runtime state tree."""
    inspect_cmd.cmd_inspect(project_path, section)

@app.command()
def why(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Explain why the runtime is in its current state."""
    inspect_cmd.cmd_why(project_path)

@app.command()
def explain(
    project_path: str = typer.Argument(".", help="Path to the project"),
    topic: str = typer.Argument("system", help="Topic: system, score, decision, or 'hypothesis <id>'"),
):
    """Explain a decision, hypothesis, or system state."""
    inspect_cmd.cmd_explain(project_path, topic)

@app.command()
def history(
    project_path: str = typer.Argument(".", help="Path to the project"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of events"),
):
    """Show recent runtime history."""
    inspect_cmd.cmd_history(project_path, limit)


universe_typer = typer.Typer(name="universe", help="Universe management commands")
app.add_typer(universe_typer)

@universe_typer.command()
def init(
    project_path: str = typer.Argument(".", help="Path to the project"),
    name: str = typer.Option("default", "--name", "-n", help="Universe name"),
):
    """Initialize a SRIE Universe."""
    universe_cmd.cmd_init(project_path, name)

@universe_typer.command()
def status(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Show universe status."""
    universe_cmd.cmd_status(project_path)

@universe_typer.command()
def org(
    project_path: str = typer.Argument(".", help="Path to the project"),
    name: str = typer.Argument("default", help="Organization name"),
):
    """Register an organization."""
    universe_cmd.cmd_org_add(project_path, name)

@universe_typer.command()
def workspace(
    project_path: str = typer.Argument(".", help="Path to the project"),
    name: str = typer.Argument("default", help="Workspace name"),
    org: str = typer.Option(None, "--org", help="Parent organization ID"),
):
    """Register a workspace."""
    universe_cmd.cmd_ws_add(project_path, name, org)

@universe_typer.command()
def project(
    project_path: str = typer.Argument(".", help="Path to the project"),
    name: str = typer.Argument("default", help="Project name"),
    workspace: str = typer.Option(None, "--workspace", help="Parent workspace ID"),
):
    """Register a project."""
    universe_cmd.cmd_project_add(project_path, name, workspace)

@universe_typer.command()
def chain(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Show ownership chain."""
    universe_cmd.cmd_chain(project_path)

@universe_typer.command()
def twin(
    project_path: str = typer.Argument(".", help="Path to the project"),
):
    """Show Universe Digital Twin."""
    universe_cmd.cmd_twin(project_path)


studio_typer = typer.Typer(name="studio", help="Mission Control commands")
app.add_typer(studio_typer)

@studio_typer.command()
def serve(
    project_path: str = typer.Argument(".", help="Path to the project"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind"),
    port: int = typer.Option(5000, "--port", "-p", help="Port to bind"),
):
    """Start SRIE Mission Control web interface."""
    studio_cmd.cmd_serve(project_path, host, port)


if __name__ == "__main__":
    app()
