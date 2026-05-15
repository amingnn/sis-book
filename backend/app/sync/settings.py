from collections.abc import Callable
from pathlib import Path

from app.sync.json_store import read_json, write_json


def default_settings(
    detect_dirs: Callable[[], list[dict]],
    get_sync_root: Callable[[str], Path],
) -> dict:
    return {
        "sync_base_dir": "",
        "enabled": False,
        "interval_minutes": 30,
        "last_sync_at": "",
        "last_sync_direction": "",
        "last_error": "",
    }


def get_settings(
    settings_path: Path,
    detect_dirs: Callable[[], list[dict]],
    get_sync_root: Callable[[str], Path],
) -> dict:
    payload = default_settings(detect_dirs, get_sync_root)
    payload.update(read_json(settings_path, {}))
    return payload


def save_settings(
    settings_path: Path,
    *,
    sync_base_dir: str,
    enabled: bool,
    interval_minutes: int,
    current_settings: dict,
    get_sync_root: Callable[[str], Path],
) -> dict:
    normalized_dir = str(get_sync_root(sync_base_dir.strip())) if sync_base_dir.strip() else ""
    current_settings.update(
        {
            "sync_base_dir": normalized_dir,
            "enabled": enabled,
            "interval_minutes": interval_minutes,
        }
    )
    write_json(settings_path, current_settings)
    return current_settings
