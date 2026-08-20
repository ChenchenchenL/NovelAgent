from __future__ import annotations

import argparse
import threading
import webbrowser

import uvicorn

from .api import create_app
from .config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description="NovelAgent Main Application Entry")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    app = create_app(Settings())
    threading.Timer(0.8, lambda: webbrowser.open(f"http://{args.host}:{args.port}")).start()
    uvicorn.run(app, host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
