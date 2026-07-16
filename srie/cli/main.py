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


if __name__ == "__main__":
    app()
