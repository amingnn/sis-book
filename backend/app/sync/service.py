import json
import os
import platform
import shutil
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

from app.config import APP_NAME, DATABASE_PATH, get_data_dir
from app.database import export_database_snapshot, replace_database_from

SYNC_DIR_NAME = "sis-book-sync"
SETTINGS_PATH = get_data_dir() / "sync_settings.json"
STATE_PATH = get_data_dir() / "sync_state.json"
IMAGES_DIR = get_data_dir() / "img"
_sync_lock = threading.Lock()
_scheduler_thread: threading.Thread | None = None
_scheduler_stop_event = threading.Event()


class SyncError(Exception):
    pass


def _now_iso() -> str:
    return datetime.now().isoformat()


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _default_settings() -> dict:
    candidates = detect_onedrive_dirs()
    initial_dir = str(_get_sync_root(candidates[0]["path"])) if candidates else ""
    return {
        "sync_base_dir": initial_dir,
        "enabled": False,
        "interval_minutes": 30,
        "last_sync_at": "",
        "last_sync_direction": "",
        "last_error": "",
    }


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
    return _read_json(
        STATE_PATH,
        {
            "last_local_signature": "",
            "last_remote_signature": "",
        },
    )


def _write_state(payload: dict) -> None:
    _write_json(STATE_PATH, payload)


def _get_sync_root(base_dir: str) -> Path:
    if not base_dir:
        raise SyncError("请先选择同步目录")
    path = Path(base_dir).expanduser()
    if path.name == SYNC_DIR_NAME:
        return path
    return path / SYNC_DIR_NAME


def _get_remote_snapshot_dir(base_dir: str) -> Path:
    return _get_sync_root(base_dir) / "current"


def _get_remote_manifest_path(base_dir: str) -> Path:
    return _get_sync_root(base_dir) / "manifest.json"


def _list_files(root: Path) -> list[dict]:
    if not root.exists():
        return []
    files: list[dict] = []
    for file_path in sorted(path for path in root.rglob("*") if path.is_file()):
        stat = file_path.stat()
        files.append(
            {
                "path": file_path.relative_to(root).as_posix(),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    return files


def _build_signature(db_meta: dict, image_files: list[dict]) -> str:
    return json.dumps({"db": db_meta, "images": image_files}, ensure_ascii=False, sort_keys=True)


def _collect_local_meta() -> dict:
    db_stat = DATABASE_PATH.stat()
    image_files = _list_files(IMAGES_DIR)
    db_meta = {
        "size": db_stat.st_size,
        "mtime_ns": db_stat.st_mtime_ns,
    }
    latest_image_mtime = max((file["mtime_ns"] for file in image_files), default=0)
    return {
        "app": APP_NAME,
        "device_name": platform.node(),
        "content_updated_at_ns": max(db_meta["mtime_ns"], latest_image_mtime),
        "db": db_meta,
        "images": {"count": len(image_files), "files": image_files},
        "signature": _build_signature(db_meta, image_files),
    }


def _read_remote_manifest(base_dir: str) -> dict | None:
    manifest_path = _get_remote_manifest_path(base_dir)
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _mirror_directory(source_dir: Path, target_dir: Path) -> None:
    source_files = {
        file["path"]: file
        for file in _list_files(source_dir)
    }
    target_files = {
        file["path"]: file
        for file in _list_files(target_dir)
    }

    target_dir.mkdir(parents=True, exist_ok=True)

    for relative_path, source_file in source_files.items():
        source_path = source_dir / relative_path
        target_path = target_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_file = target_files.get(relative_path)
        if (
            target_file
            and target_file["size"] == source_file["size"]
            and target_file["mtime_ns"] == source_file["mtime_ns"]
        ):
            continue
        shutil.copy2(source_path, target_path)

    for relative_path in sorted(set(target_files) - set(source_files), reverse=True):
        target_path = target_dir / relative_path
        if target_path.exists():
            target_path.unlink()

    for path in sorted((path for path in target_dir.rglob("*") if path.is_dir()), reverse=True):
        if not any(path.iterdir()):
            path.rmdir()


def _write_remote_snapshot(base_dir: str, local_meta: dict) -> dict:
    sync_root = _get_sync_root(base_dir)
    remote_snapshot_dir = _get_remote_snapshot_dir(base_dir)
    remote_images_dir = remote_snapshot_dir / "img"
    temp_dir = Path(tempfile.mkdtemp(prefix="sis-book-sync-", dir=get_data_dir()))
    try:
        temp_db_path = temp_dir / "data.db"
        export_database_snapshot(temp_db_path)

        sync_root.mkdir(parents=True, exist_ok=True)
        remote_snapshot_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(temp_db_path, remote_snapshot_dir / "data.db")
        _mirror_directory(IMAGES_DIR, remote_images_dir)

        manifest = {
            **local_meta,
            "synced_at": _now_iso(),
            "sync_dir_name": SYNC_DIR_NAME,
        }
        _write_json(_get_remote_manifest_path(base_dir), manifest)
        return manifest
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _restore_remote_snapshot(base_dir: str, manifest: dict) -> None:
    remote_snapshot_dir = _get_remote_snapshot_dir(base_dir)
    remote_db_path = remote_snapshot_dir / "data.db"
    remote_images_dir = remote_snapshot_dir / "img"
    if not remote_db_path.exists():
        raise SyncError("同步目录中缺少数据库快照")

    replace_database_from(remote_db_path)
    _mirror_directory(remote_images_dir, IMAGES_DIR)
    latest_db_mtime_ns = remote_db_path.stat().st_mtime_ns
    if latest_db_mtime_ns:
        os.utime(DATABASE_PATH, ns=(latest_db_mtime_ns, latest_db_mtime_ns))

    for image in manifest.get("images", {}).get("files", []):
        local_path = IMAGES_DIR / image["path"]
        if local_path.exists():
            os.utime(local_path, ns=(image["mtime_ns"], image["mtime_ns"]))


def detect_onedrive_dirs() -> list[dict]:
    candidates: list[Path] = []
    env_names = ["OneDrive", "OneDriveCommercial", "OneDriveConsumer"]
    for name in env_names:
        value = os.environ.get(name)
        if value:
            candidates.append(Path(value).expanduser())

    home = Path.home()
    guessed_paths = [
        home / "OneDrive",
        home / "OneDrive - Personal",
        home / "Library" / "CloudStorage" / "OneDrive-Personal",
        home / "Library" / "CloudStorage" / "OneDrive",
    ]
    guessed_paths.extend((home / "Library" / "CloudStorage").glob("OneDrive*"))
    guessed_paths.extend(home.glob("OneDrive*"))

    for candidate in guessed_paths:
        candidates.append(candidate)

    seen: set[str] = set()
    results: list[dict] = []
    for candidate in candidates:
        resolved = str(candidate.expanduser())
        if resolved in seen or not candidate.exists() or not candidate.is_dir():
            continue
        seen.add(resolved)
        results.append({"path": resolved, "label": candidate.name})
    return results


def choose_sync_dir() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askdirectory()
        root.destroy()
        return str(selected) if selected else ""
    except Exception as exc:
        raise SyncError("打开目录选择失败，请手动输入路径") from exc


def _choose_sync_direction(local_meta: dict, remote_manifest: dict | None, state: dict) -> str:
    if remote_manifest is None:
        return "push"

    remote_changed = remote_manifest.get("signature", "") != state.get("last_remote_signature", "")
    local_changed = local_meta.get("signature", "") != state.get("last_local_signature", "")

    if remote_changed and not local_changed:
        return "pull"
    if local_changed and not remote_changed:
        return "push"
    if remote_changed and local_changed:
        return "conflict"
    return "noop"


def run_sync(trigger: str = "manual", force_direction: str | None = None) -> dict:
    if not _sync_lock.acquire(blocking=False):
        raise SyncError("同步正在执行，请稍后再试")

    settings = get_settings()
    base_dir = settings.get("sync_base_dir", "").strip()
    if not base_dir:
        raise SyncError("请先配置同步目录")

    try:
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
        settings["last_error"] = str(exc)
        _write_json(SETTINGS_PATH, settings)
        if isinstance(exc, SyncError):
            raise
        raise SyncError(f"同步失败：{exc}") from exc
    finally:
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
