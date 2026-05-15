import json
import os
import platform
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path

from app.config import APP_NAME, DATABASE_PATH, DATA_DIR
from app.database import export_database_snapshot, replace_database_from
from app.sync.errors import SyncError
from app.sync.files import list_files, mirror_directory
from app.sync.json_store import write_json


def build_signature(db_meta: dict, image_files: list[dict]) -> str:
    return json.dumps({"db": db_meta, "images": image_files}, ensure_ascii=False, sort_keys=True)


def collect_local_meta(images_dir: Path) -> dict:
    db_stat = DATABASE_PATH.stat()
    image_files = list_files(images_dir)
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
        "signature": build_signature(db_meta, image_files),
    }


def read_remote_manifest(get_remote_manifest_path: Callable[[str], Path], base_dir: str) -> dict | None:
    manifest_path = get_remote_manifest_path(base_dir)
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def write_remote_snapshot(
    *,
    base_dir: str,
    local_meta: dict,
    images_dir: Path,
    get_sync_root: Callable[[str], Path],
    get_remote_snapshot_dir: Callable[[str], Path],
    get_remote_manifest_path: Callable[[str], Path],
    now_iso: Callable[[], str],
) -> dict:
    sync_root = get_sync_root(base_dir)
    remote_snapshot_dir = get_remote_snapshot_dir(base_dir)
    remote_images_dir = remote_snapshot_dir / "img"
    temp_dir = Path(tempfile.mkdtemp(prefix="sis-book-sync-", dir=DATA_DIR))
    try:
        temp_db_path = temp_dir / "data.db"
        export_database_snapshot(temp_db_path)

        sync_root.mkdir(parents=True, exist_ok=True)
        remote_snapshot_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(temp_db_path, remote_snapshot_dir / "data.db")
        mirror_directory(images_dir, remote_images_dir)

        manifest = {
            **local_meta,
            "synced_at": now_iso(),
            "sync_dir_name": sync_root.name,
        }
        write_json(get_remote_manifest_path(base_dir), manifest)
        return manifest
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def restore_remote_snapshot(
    *,
    base_dir: str,
    manifest: dict,
    images_dir: Path,
    get_remote_snapshot_dir: Callable[[str], Path],
) -> None:
    remote_snapshot_dir = get_remote_snapshot_dir(base_dir)
    remote_db_path = remote_snapshot_dir / "data.db"
    remote_images_dir = remote_snapshot_dir / "img"
    if not remote_db_path.exists():
        raise SyncError("同步目录中缺少数据库快照")

    replace_database_from(remote_db_path)
    mirror_directory(remote_images_dir, images_dir)
    latest_db_mtime_ns = remote_db_path.stat().st_mtime_ns
    if latest_db_mtime_ns:
        os.utime(DATABASE_PATH, ns=(latest_db_mtime_ns, latest_db_mtime_ns))

    for image in manifest.get("images", {}).get("files", []):
        local_path = images_dir / image["path"]
        if local_path.exists():
            os.utime(local_path, ns=(image["mtime_ns"], image["mtime_ns"]))
