import threading
import time
from datetime import datetime

from app.sync.discovery import choose_sync_dir, detect_onedrive_dirs
from app.sync.errors import SyncError
from app.sync.files import list_files as _list_files
from app.sync.files import mirror_directory as _mirror_directory
from app.sync.json_store import read_json as _read_json
from app.sync.json_store import write_json as _write_json
from app.sync.paths import (
    IMAGES_DIR,
    SETTINGS_PATH,
    STATE_PATH,
    SYNC_DIR_NAME,
    get_remote_manifest_path as _get_remote_manifest_path,
    get_remote_snapshot_dir as _get_remote_snapshot_dir,
    get_sync_root as _get_sync_root,
)
from app.sync.planner import choose_sync_direction as _choose_sync_direction
from app.sync.snapshot import build_signature as _build_signature
from app.sync.snapshot import collect_local_meta
from app.sync.snapshot import read_remote_manifest
from app.sync.snapshot import restore_remote_snapshot
from app.sync.snapshot import write_remote_snapshot
from app.sync.settings import default_settings as _build_default_settings
from app.sync.state import get_state
from app.sync.state import write_state

_sync_lock = threading.Lock()
_scheduler_thread: threading.Thread | None = None
_scheduler_stop_event = threading.Event()


def _now_iso() -> str:
    return datetime.now().isoformat()


def _default_settings() -> dict:
    return _build_default_settings(detect_onedrive_dirs, _get_sync_root)


def get_settings() -> dict:
    payload = _default_settings()
    payload.update(_read_json(SETTINGS_PATH, {}))
    return payload


def save_settings(sync_base_dir: str, enabled: bool, interval_minutes: int) -> dict:
    payload = get_settings()
    normalized_dir = str(_get_sync_root(sync_base_dir.strip())) if sync_base_dir.strip() else ""
    payload.update(
        {
            "sync_base_dir": normalized_dir,
            "enabled": enabled,
            "interval_minutes": interval_minutes,
        }
    )
    _write_json(SETTINGS_PATH, payload)
    return payload


def _get_state() -> dict:
    return get_state(STATE_PATH)


def _write_state(payload: dict) -> None:
    write_state(STATE_PATH, payload)


def _collect_local_meta() -> dict:
    return collect_local_meta(IMAGES_DIR)


def _read_remote_manifest(base_dir: str) -> dict | None:
    return read_remote_manifest(_get_remote_manifest_path, base_dir)


def _write_remote_snapshot(base_dir: str, local_meta: dict) -> dict:
    return write_remote_snapshot(
        base_dir=base_dir,
        local_meta=local_meta,
        images_dir=IMAGES_DIR,
        get_sync_root=_get_sync_root,
        get_remote_snapshot_dir=_get_remote_snapshot_dir,
        get_remote_manifest_path=_get_remote_manifest_path,
        now_iso=_now_iso,
    )


def _restore_remote_snapshot(base_dir: str, manifest: dict) -> None:
    restore_remote_snapshot(
        base_dir=base_dir,
        manifest=manifest,
        images_dir=IMAGES_DIR,
        get_remote_snapshot_dir=_get_remote_snapshot_dir,
    )


def run_sync(trigger: str = "manual", force_direction: str | None = None) -> dict:
    if not _sync_lock.acquire(blocking=False):
        raise SyncError("同步正在执行，请稍后再试")

    settings: dict = {}
    try:
        settings = get_settings()
        base_dir = settings.get("sync_base_dir", "").strip()
        if not base_dir:
            raise SyncError("请先配置同步目录")

        local_meta = _collect_local_meta()
        remote_manifest = _read_remote_manifest(base_dir)
        state = _get_state()
        direction = _choose_sync_direction(local_meta, remote_manifest, state)
        if direction == "conflict" and force_direction in {"push", "pull"}:
            direction = force_direction

        if direction == "conflict":
            remote_updated = remote_manifest.get("content_updated_at_ns", 0) if remote_manifest else 0
            local_updated = local_meta.get("content_updated_at_ns", 0)
            return {
                "ok": False,
                "direction": "conflict",
                "trigger": trigger,
                "sync_root": str(_get_sync_root(base_dir)),
                "last_sync_at": settings.get("last_sync_at", ""),
                "conflict": {
                    "local_updated_at_ns": local_updated,
                    "remote_updated_at_ns": remote_updated,
                    "local_device_name": local_meta.get("device_name", ""),
                    "remote_device_name": (remote_manifest or {}).get("device_name", ""),
                },
            }

        if direction == "push":
            remote_manifest = _write_remote_snapshot(base_dir, local_meta)
            state["last_local_signature"] = local_meta["signature"]
            state["last_remote_signature"] = local_meta["signature"]
        elif direction == "pull":
            if remote_manifest is None:
                raise SyncError("同步目录中没有可恢复的数据")
            _restore_remote_snapshot(base_dir, remote_manifest)
            state["last_local_signature"] = remote_manifest["signature"]
            state["last_remote_signature"] = remote_manifest["signature"]

        _write_state(state)

        settings.update(
            {
                "last_sync_at": _now_iso(),
                "last_sync_direction": direction,
                "last_error": "",
            }
        )
        _write_json(SETTINGS_PATH, settings)
        return {
            "ok": True,
            "direction": direction,
            "trigger": trigger,
            "sync_root": str(_get_sync_root(base_dir)),
            "last_sync_at": settings["last_sync_at"],
            "conflict": None,
        }
    except Exception as exc:
        if settings:
            settings["last_error"] = str(exc)
            _write_json(SETTINGS_PATH, settings)
        if isinstance(exc, SyncError):
            raise
        raise SyncError(f"同步失败：{exc}") from exc
    finally:
        if _sync_lock.locked():
            _sync_lock.release()


def get_status() -> dict:
    settings = get_settings()
    base_dir = settings.get("sync_base_dir", "").strip()
    normalized_dir = str(_get_sync_root(base_dir)) if base_dir else ""
    return {
        **settings,
        "sync_base_dir": normalized_dir,
        "detected_dirs": detect_onedrive_dirs(),
        "sync_root": normalized_dir,
        "configured": bool(base_dir),
    }


def _scheduler_loop() -> None:
    while not _scheduler_stop_event.wait(60):
        settings = get_settings()
        if not settings.get("enabled") or not settings.get("sync_base_dir"):
            continue

        interval_seconds = int(settings.get("interval_minutes", 30)) * 60
        last_sync_at = settings.get("last_sync_at", "")
        if last_sync_at:
            try:
                elapsed = time.time() - datetime.fromisoformat(last_sync_at).timestamp()
                if elapsed < interval_seconds:
                    continue
            except ValueError:
                pass

        try:
            run_sync(trigger="auto")
        except SyncError:
            continue


def start_scheduler() -> None:
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _scheduler_stop_event.clear()
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()


def stop_scheduler() -> None:
    _scheduler_stop_event.set()
