from pathlib import Path

import pytest

from app import config


def test_get_data_dir_uses_env_path(monkeypatch, tmp_path):
    custom_dir = tmp_path / "custom-data"
    monkeypatch.setenv("SIS_BOOK_DATA", str(custom_dir))

    data_dir = config.get_data_dir()

    assert data_dir == custom_dir
    assert data_dir.is_dir()


def test_get_data_dir_uses_platform_default(monkeypatch, tmp_path):
    default_dir = tmp_path / "platform-data"
    monkeypatch.delenv("SIS_BOOK_DATA", raising=False)

    def fake_user_data_dir(app_name, appauthor=None):
        assert appauthor is False
        return str(default_dir / app_name)

    monkeypatch.setattr(config, "user_data_dir", fake_user_data_dir)

    data_dir = config.get_data_dir("demo-book")
    assert data_dir == default_dir / "demo-book"
    assert data_dir.is_dir()


def test_get_data_dir_is_idempotent(monkeypatch, tmp_path):
    custom_dir = tmp_path / "idempotent"
    monkeypatch.setenv("SIS_BOOK_DATA", str(custom_dir))

    first_dir = config.get_data_dir()
    second_dir = config.get_data_dir()

    assert first_dir == second_dir
    assert second_dir.is_dir()


def test_get_data_dir_raises_when_mkdir_fails(monkeypatch, tmp_path):
    custom_dir = tmp_path / "blocked"
    monkeypatch.setenv("SIS_BOOK_DATA", str(custom_dir))

    def failing_mkdir(self, *args, **kwargs):
        raise PermissionError("no permission to create directory")

    monkeypatch.setattr(Path, "mkdir", failing_mkdir)

    with pytest.raises(PermissionError, match="no permission"):
        config.get_data_dir()


def test_get_data_dir_raises_when_target_is_file(monkeypatch, tmp_path):
    data_file = tmp_path / "data-file"
    data_file.write_text("not a directory")
    monkeypatch.setenv("SIS_BOOK_DATA", str(data_file))

    with pytest.raises(FileExistsError):
        config.get_data_dir()
