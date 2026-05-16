import sys
from pathlib import Path

from app.dashboard.service import get_dashboard
from app.factory import create_app
from app.logging import logger
from app.server import ensure_stdio_for_frozen_app, run_desktop_app, run_dev_server
from app.static import get_base_dir


def _get_base_dir() -> Path:
    """打包后用 sys._MEIPASS，开发时用项目根目录。"""
    return get_base_dir(Path(__file__))


ensure_stdio_for_frozen_app()
app = create_app(_get_base_dir())


def main() -> None:
    logger.info("启动入口调用，argv={}，frozen={}", sys.argv, getattr(sys, "frozen", False))
    port = 18234
    if "--dev" in sys.argv:
        run_dev_server(port)
        return
    run_desktop_app(app, port)


if __name__ == "__main__":
    main()
