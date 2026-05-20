import base64
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI

from app.logging import logger


def ensure_stdio_for_frozen_app() -> None:
    if getattr(sys, "frozen", False) and sys.stdout is None:
        import os

        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")


def start_server(app: FastAPI, port: int = 18234) -> None:
    try:
        logger.info("启动 uvicorn 服务，端口 {}", port)
        uvicorn.run(app, host="127.0.0.1", port=port, log_config=None)
    except Exception:
        logger.exception("uvicorn 服务异常退出")


def wait_for_backend(port: int, path: str = "/api/dashboard", timeout_seconds: int = 15) -> bool:
    logger.info("等待后端服务就绪")
    attempts = timeout_seconds * 10
    for index in range(attempts):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=1)
            logger.info("后端服务已就绪，耗时 {:.1f}s", index * 0.1)
            return True
        except Exception:
            time.sleep(0.1)
    logger.warning("后端服务在 {}s 内未就绪，继续打开窗口", timeout_seconds)
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
            logger.exception("桌面端保存文件失败")
            return {"saved": False, "error": "保存文件失败"}


def run_desktop_app(app: FastAPI, port: int = 18234) -> None:
    server_thread = threading.Thread(target=start_server, args=(app, port), daemon=True)
    server_thread.start()
    ready = wait_for_backend(port)

    try:
        import webview

        window_url = f"http://127.0.0.1:{port}"
        logger.info("创建桌面窗口，url={}，backend_ready={}", window_url, ready)
        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.create_window(
            "暮橙体育记账本",
            window_url,
            js_api=DesktopApi(),
            width=1280,
            height=800,
            min_size=(1024, 600),
        )
        webview.start()
        logger.info("桌面窗口已退出")
    except Exception:
        logger.exception("桌面窗口初始化失败")
        raise


def run_dev_server(port: int = 18234) -> None:
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
