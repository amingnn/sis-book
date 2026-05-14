import sys
import threading
import time
import traceback
import urllib.request

import uvicorn
from fastapi import FastAPI

from app.debug import log


def ensure_stdio_for_frozen_app() -> None:
    if getattr(sys, "frozen", False) and sys.stdout is None:
        import os

        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")


def start_server(app: FastAPI, port: int = 18234) -> None:
    try:
        log(f"start_server: starting uvicorn on port {port}")
        uvicorn.run(app, host="127.0.0.1", port=port, log_config=None)
    except Exception:
        log(f"start_server CRASHED: {traceback.format_exc()}")


def wait_for_backend(port: int, path: str = "/api/dashboard", timeout_seconds: int = 15) -> bool:
    log("waiting for backend to be ready...")
    attempts = timeout_seconds * 10
    for index in range(attempts):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=1)
            log(f"backend ready after {index * 0.1:.1f}s")
            return True
        except Exception:
            time.sleep(0.1)
    log(f"WARNING: backend NOT ready after {timeout_seconds}s, opening window anyway")
    return False


def run_desktop_app(app: FastAPI, port: int = 18234) -> None:
    server_thread = threading.Thread(target=start_server, args=(app, port), daemon=True)
    server_thread.start()
    wait_for_backend(port)

    import webview

    webview.create_window(
        "暮橙体育记账本",
        f"http://127.0.0.1:{port}",
        width=1280,
        height=800,
        min_size=(1024, 600),
    )
    webview.start()


def run_dev_server(port: int = 18234) -> None:
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
