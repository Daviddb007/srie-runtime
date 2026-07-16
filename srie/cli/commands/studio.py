from srie.mission_control.app import app as flask_app, init_app
from srie.sdk.client import SDK
from pathlib import Path


def cmd_serve(project_path: str = ".", host: str = "127.0.0.1", port: int = 5000):
    sdk = SDK(project_path)
    sdk.init()
    init_app(sdk)
    print(f"SRIE Mission Control starting at http://{host}:{port}")
    print(f"Project: {Path(project_path).resolve()}")
    print("Rooms: Universe, Operations, Intelligence, Knowledge, Governance")
    flask_app.run(host=host, port=port, debug=True)
