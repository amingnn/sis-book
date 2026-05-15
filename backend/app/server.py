import base64
import sys
import threading
import time
import traceback
import urllib.request
from pathlib import Path
from typing import Any

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


class DesktopApi:
    def save_file(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            import webview

            filename = str(payload.get("filename") or "export")
            data_url = str(payload.get("data_url") or payload.get("dataUrl") or "")
            file_types = tuple(payload.get("file_types") or payload.get("fileTypes") or ())
            if not data_url:
                return {"saved": False, "error": "没有可保存的数据"}

            window = webview.active_window() or (webview.windows[0] if webview.windows else None)
            if window is None:
                return {"saved": False, "error": "桌面窗口未就绪"}

            dialog_type = webview.FileDialog.SAVE
            selected = window.create_file_dialog(
                dialog_type,
                save_filename=filename,
                file_types=file_types,
            )
            if not selected:
                return {"saved": False, "cancelled": True}

            selected_path = selected if isinstance(selected, str) else selected[0]
            target_path = Path(selected_path)
            default_suffix = Path(filename).suffix
            if default_suffix and not target_path.suffix:
                target_path = target_path.with_suffix(default_suffix)

            payload_text = data_url.split(",", 1)[1] if "," in data_url else data_url
            target_path.write_bytes(base64.b64decode(payload_text))
            return {"saved": True, "path": str(target_path)}
        except Exception:
            log(f"DesktopApi.save_file failed: {traceback.format_exc()}")
            return {"saved": False, "error": "保存文件失败"}


def run_desktop_app(app: FastAPI, port: int = 18234) -> None:
    server_thread = threading.Thread(target=start_server, args=(app, port), daemon=True)
    server_thread.start()
    wait_for_backend(port)

    import webview

    webview.settings["ALLOW_DOWNLOADS"] = True
    webview.create_window(
        "暮橙体育记账本",
        f"http://127.0.0.1:{port}",
        js_api=DesktopApi(),
        width=1280,
        height=800,
        min_size=(1024, 600),
    )
    webview.start()


def run_dev_server(port: int = 18234) -> None:
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
