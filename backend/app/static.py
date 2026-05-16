import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import IMG_DIR
from app.logging import logger


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and self._should_fallback_to_index(path):
                return await super().get_response("index.html", scope)
            raise

    @staticmethod
    def _should_fallback_to_index(path: str) -> bool:
        if path in {"api", "img", "assets"}:
            return False
        if path.startswith(("api/", "img/", "assets/")):
            return False
        return Path(path).suffix == ""


def get_base_dir(entry_file: Path) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore
    return entry_file.parent.parent


def mount_static_files(app: FastAPI, base_dir: Path) -> None:
    frontend_dist = base_dir / "frontend" / "dist"
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(
        "静态资源挂载检查：frozen={}，base_dir={}，frontend_dist={}，exists={}",
        getattr(sys, "frozen", False),
        base_dir,
        frontend_dist,
        frontend_dist.exists(),
    )

    app.mount("/img", StaticFiles(directory=str(IMG_DIR)), name="images")

    if frontend_dist.exists():
        app.mount("/", SPAStaticFiles(directory=str(frontend_dist), html=True), name="static")
        logger.info("前端静态资源已挂载")
    else:
        logger.warning("未找到前端 dist，跳过静态资源挂载")
