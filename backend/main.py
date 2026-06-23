import sys

from app.dashboard.service import get_dashboard
from app.factory import create_app
from app.logging import logger
from app.paths import get_resource_root
from app.server import ensure_stdio_for_frozen_app, run_desktop_app, run_dev_server


def _get_base_dir():
    return get_resource_root()


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
