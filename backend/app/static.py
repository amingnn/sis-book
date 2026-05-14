import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_data_dir
from app.debug import log


def get_base_dir(entry_file: Path) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return entry_file.parent.parent


def mount_static_files(app: FastAPI, base_dir: Path) -> None:
    frontend_dist = base_dir / "frontend" / "dist"
    images_dir = get_data_dir() / "img"
    images_dir.mkdir(parents=True, exist_ok=True)
    log(
        "frozen="
        f"{getattr(sys, 'frozen', False)}, BASE_DIR={base_dir}, "
        f"frontend_dist={frontend_dist}, exists={frontend_dist.exists()}"
    )

    app.mount("/img", StaticFiles(directory=str(images_dir)), name="images")

    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
        log("frontend static files mounted")
    else:
        log("WARNING: frontend dist NOT FOUND, static files not mounted")
