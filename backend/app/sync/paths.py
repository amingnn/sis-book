from pathlib import Path

from app.config import DATA_DIR, IMG_DIR
from app.sync.errors import SyncError

SYNC_DIR_NAME = "sis-book-sync"
SETTINGS_PATH = DATA_DIR / "sync_settings.json"
STATE_PATH = DATA_DIR / "sync_state.json"
IMAGES_DIR = IMG_DIR


def get_sync_root(base_dir: str) -> Path:
    if not base_dir:
        raise SyncError("请先选择同步目录")
    path = Path(base_dir).expanduser()
    if path.name == SYNC_DIR_NAME:
        return path
    return path / SYNC_DIR_NAME


def get_remote_snapshot_dir(base_dir: str) -> Path:
    return get_sync_root(base_dir) / "current"


def get_remote_manifest_path(base_dir: str) -> Path:
    return get_sync_root(base_dir) / "manifest.json"
