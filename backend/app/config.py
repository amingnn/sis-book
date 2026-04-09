import sys
from pathlib import Path


def get_data_dir() -> Path:
    """获取数据存储目录，根据操作系统选择合适路径"""
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"

    data_dir = base / "sis-book"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


DATABASE_URL = f"sqlite:///{get_data_dir() / 'data.db'}"
