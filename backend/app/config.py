import sys
from pathlib import Path

APP_NAME = "sis-book"


def get_data_dir() -> Path:
    """获取数据存储目录，根据操作系统选择合适路径"""
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"

    data_dir = base / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


DATABASE_PATH = get_data_dir() / "data.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
