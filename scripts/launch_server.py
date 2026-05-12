from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Audio Language server.")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host to bind. Default: {DEFAULT_HOST}")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to bind. Default: {DEFAULT_PORT}")
    parser.add_argument(
        "--no-port-fallback",
        action="store_true",
        help="Fail instead of trying the next port when the requested port is busy.",
    )
    parser.add_argument("--reload", action="store_true", help="Restart the server when backend files change.")
    return parser.parse_args()


def find_available_port(host: str, start_port: int, allow_fallback: bool) -> int:
    port = start_port

    while True:
        if is_port_available(host, port):
            return port

        if not allow_fallback:
            raise SystemExit(f"Port {port} is already in use on {host}.")

        port += 1


def is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False

    return True


def main() -> None:
    args = parse_args()
    project_dir = Path(__file__).resolve().parent.parent
    backend_dir = project_dir / "backend"

    sys.path.insert(0, str(backend_dir))
    sys.path.insert(0, str(project_dir))

    from scripts.load_secrets import load_secrets

    load_secrets()

    port = find_available_port(
        host=args.host,
        start_port=args.port,
        allow_fallback=not args.no_port_fallback,
    )
    url = f"http://{args.host}:{port}"

    print(f"Starting Audio Language server at {url}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: uvicorn. Install backend dependencies with "
            "`python -m pip install -r backend/requirements.txt`."
        ) from exc

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=port,
        reload=args.reload,
        app_dir=str(backend_dir),
    )


if __name__ == "__main__":
    main()
