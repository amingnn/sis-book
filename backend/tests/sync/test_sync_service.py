import json
import threading
from pathlib import Path

import pytest

from app.sync import service as sync_service


def test_get_sync_root_normalizes_directory_name():
    assert sync_service._get_sync_root("/tmp/demo") == Path("/tmp/demo") / sync_service.SYNC_DIR_NAME
    assert sync_service._get_sync_root(f"/tmp/{sync_service.SYNC_DIR_NAME}") == Path(
        f"/tmp/{sync_service.SYNC_DIR_NAME}"
    )


def test_get_sync_root_requires_base_dir():
    with pytest.raises(sync_service.SyncError, match="请先选择同步目录"):
        sync_service._get_sync_root("")


def test_list_files_returns_sorted_relative_file_metadata(tmp_path):
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    nested = tmp_path / "a" / "c.txt"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text("cc", encoding="utf-8")

    files = sync_service._list_files(tmp_path)

    assert [item["path"] for item in files] == ["a/c.txt", "b.txt"]
    assert files[0]["size"] == 2


def test_build_signature_is_stable_for_same_payload():
    db_meta = {"size": 1, "mtime_ns": 2}
    image_files = [{"path": "img/a.png", "size": 3, "mtime_ns": 4}]

    assert sync_service._build_signature(db_meta, image_files) == json.dumps(
        {"db": db_meta, "images": image_files},
        ensure_ascii=False,
        sort_keys=True,
    )


@pytest.mark.parametrize(
    ("remote_manifest", "state", "expected"),
    [
        (None, {"last_local_signature": "", "last_remote_signature": ""}, "push"),
        (
            {"signature": "remote-new"},
            {"last_local_signature": "local-current", "last_remote_signature": "remote-old"},
            "pull",
        ),
        (
            {"signature": "remote-current"},
            {"last_local_signature": "local-old", "last_remote_signature": "remote-current"},
            "push",
        ),
        (
            {"signature": "remote-new"},
            {"last_local_signature": "local-old", "last_remote_signature": "remote-old"},
            "conflict",
        ),
        (
            {"signature": "same"},
            {"last_local_signature": "same", "last_remote_signature": "same"},
            "noop",
        ),
    ],
)
def test_choose_sync_direction_covers_all_paths(remote_manifest, state, expected):
    local_meta = {"signature": "local-current" if expected != "noop" else "same"}

    assert sync_service._choose_sync_direction(local_meta, remote_manifest, state) == expected


def test_save_settings_and_get_status_normalize_path(monkeypatch, tmp_path):
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(sync_service, "SETTINGS_PATH", settings_path)
    monkeypatch.setattr(sync_service, "detect_onedrive_dirs", lambda: [{"path": str(tmp_path / "OneDrive"), "label": "OneDrive"}])

    saved = sync_service.save_settings(str(tmp_path / "OneDrive"), True, 45)
    status = sync_service.get_status()

    expected_root = str(tmp_path / "OneDrive" / sync_service.SYNC_DIR_NAME)
    assert saved["sync_base_dir"] == expected_root
    assert status["sync_base_dir"] == expected_root
    assert status["sync_root"] == expected_root
    assert status["configured"] is True


def test_run_sync_push_updates_state_and_settings(monkeypatch, tmp_path):
    writes = []
    monkeypatch.setattr(sync_service, "_sync_lock", threading.Lock())
    monkeypatch.setattr(sync_service, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(
        sync_service,
        "get_settings",
        lambda: {"sync_base_dir": str(tmp_path), "last_sync_at": "", "last_error": ""},
    )
    monkeypatch.setattr(sync_service, "_collect_local_meta", lambda: {"signature": "local-new", "content_updated_at_ns": 3, "device_name": "mac"})
    monkeypatch.setattr(sync_service, "_read_remote_manifest", lambda base_dir: {"signature": "remote-old"})
    monkeypatch.setattr(sync_service, "_get_state", lambda: {"last_local_signature": "local-old", "last_remote_signature": "remote-old"})
    monkeypatch.setattr(sync_service, "_write_remote_snapshot", lambda base_dir, local_meta: {"signature": local_meta["signature"]})
    monkeypatch.setattr(sync_service, "_write_state", lambda payload: writes.append(("state", payload.copy())))
    monkeypatch.setattr(sync_service, "_write_json", lambda path, payload: writes.append(("settings", payload.copy())))
    monkeypatch.setattr(sync_service, "_now_iso", lambda: "2026-04-23T10:00:00")

    result = sync_service.run_sync()

    assert result["ok"] is True
    assert result["direction"] == "push"
    assert ("state", {"last_local_signature": "local-new", "last_remote_signature": "local-new"}) in writes
    assert any(item[0] == "settings" and item[1]["last_sync_direction"] == "push" for item in writes)


def test_run_sync_pull_restores_remote_snapshot(monkeypatch, tmp_path):
    restored = []
    monkeypatch.setattr(sync_service, "_sync_lock", threading.Lock())
    monkeypatch.setattr(sync_service, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(
        sync_service,
        "get_settings",
        lambda: {"sync_base_dir": str(tmp_path), "last_sync_at": "old", "last_error": ""},
    )
    remote_manifest = {"signature": "remote-new", "content_updated_at_ns": 9, "device_name": "pc"}
    monkeypatch.setattr(sync_service, "_collect_local_meta", lambda: {"signature": "local-old", "content_updated_at_ns": 3, "device_name": "mac"})
    monkeypatch.setattr(sync_service, "_read_remote_manifest", lambda base_dir: remote_manifest)
    monkeypatch.setattr(sync_service, "_get_state", lambda: {"last_local_signature": "local-old", "last_remote_signature": "remote-old"})
    monkeypatch.setattr(sync_service, "_restore_remote_snapshot", lambda base_dir, manifest: restored.append((base_dir, manifest)))
    monkeypatch.setattr(sync_service, "_write_state", lambda payload: None)
    monkeypatch.setattr(sync_service, "_write_json", lambda path, payload: None)
    monkeypatch.setattr(sync_service, "_now_iso", lambda: "2026-04-23T10:00:00")

    result = sync_service.run_sync()

    assert result["direction"] == "pull"
    assert restored == [(str(tmp_path), remote_manifest)]


def test_run_sync_returns_conflict_payload(monkeypatch, tmp_path):
    monkeypatch.setattr(sync_service, "_sync_lock", threading.Lock())
    monkeypatch.setattr(
        sync_service,
        "get_settings",
        lambda: {"sync_base_dir": str(tmp_path), "last_sync_at": "2026-04-22T10:00:00", "last_error": ""},
    )
    monkeypatch.setattr(sync_service, "_collect_local_meta", lambda: {"signature": "local-new", "content_updated_at_ns": 7, "device_name": "mac"})
    monkeypatch.setattr(sync_service, "_read_remote_manifest", lambda base_dir: {"signature": "remote-new", "content_updated_at_ns": 8, "device_name": "pc"})
    monkeypatch.setattr(sync_service, "_get_state", lambda: {"last_local_signature": "local-old", "last_remote_signature": "remote-old"})

    result = sync_service.run_sync()

    assert result["ok"] is False
    assert result["direction"] == "conflict"
    assert result["conflict"]["local_updated_at_ns"] == 7
    assert result["conflict"]["remote_updated_at_ns"] == 8


def test_run_sync_noop_still_updates_last_sync(monkeypatch, tmp_path):
    writes = []
    monkeypatch.setattr(sync_service, "_sync_lock", threading.Lock())
    monkeypatch.setattr(sync_service, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(
        sync_service,
        "get_settings",
        lambda: {"sync_base_dir": str(tmp_path), "last_sync_at": "", "last_error": ""},
    )
    monkeypatch.setattr(sync_service, "_collect_local_meta", lambda: {"signature": "same", "content_updated_at_ns": 3, "device_name": "mac"})
    monkeypatch.setattr(sync_service, "_read_remote_manifest", lambda base_dir: {"signature": "same"})
    monkeypatch.setattr(sync_service, "_get_state", lambda: {"last_local_signature": "same", "last_remote_signature": "same"})
    monkeypatch.setattr(sync_service, "_write_state", lambda payload: writes.append(("state", payload.copy())))
    monkeypatch.setattr(sync_service, "_write_json", lambda path, payload: writes.append(("settings", payload.copy())))
    monkeypatch.setattr(sync_service, "_now_iso", lambda: "2026-04-23T10:00:00")

    result = sync_service.run_sync()

    assert result["direction"] == "noop"
    assert any(item[0] == "settings" and item[1]["last_sync_direction"] == "noop" for item in writes)
