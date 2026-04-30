import sys
from pathlib import Path

import pytest

from app import config


@pytest.mark.parametrize(
    ("platform", "home_subpath", "expected_base_suffix"),
    [
        pytest.param(
            "win32",
            Path("Users") / "testuser",
            Path("AppData") / "Local",
            id="windows-standard-home",
        ),
        pytest.param(
            "darwin",
            Path("Users") / "macuser",
            Path("Library") / "Application Support",
            id="macos-standard-home",
        ),
        pytest.param(
            "linux",
            Path("home") / "linuxuser",
            Path(".local") / "share",
            id="linux-standard-home",
        ),
        pytest.param(
            "freebsd",
            Path("home") / "bsduser",
            Path(".local") / "share",
            id="unknown-posix-platform",
        ),
    ],
)
def test_get_data_dir_returns_expected_path(
    monkeypatch,
    tmp_path,
    platform,
    home_subpath,
    expected_base_suffix,
):
    fake_home = tmp_path / home_subpath
    fake_home.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sys, "platform", platform, raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    data_dir = config.get_data_dir()

    assert data_dir == fake_home / expected_base_suffix / config.APP_NAME
    assert data_dir.is_dir()


@pytest.mark.parametrize("platform", ["win32", "darwin", "linux"])
def test_get_data_dir_is_idempotent(monkeypatch, tmp_path, platform):
    fake_home = tmp_path / "userhome"
    fake_home.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sys, "platform", platform, raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    first_dir = config.get_data_dir()
    second_dir = config.get_data_dir()

    assert first_dir == second_dir
    assert second_dir.is_dir()


@pytest.mark.parametrize("platform", ["win32", "darwin", "linux"])
def test_get_data_dir_raises_when_mkdir_fails(monkeypatch, tmp_path, platform):
    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sys, "platform", platform, raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    def failing_mkdir(self, *args, **kwargs):
        raise PermissionError("no permission to create directory")

    monkeypatch.setattr(Path, "mkdir", failing_mkdir)

    with pytest.raises(PermissionError, match="no permission"):
        config.get_data_dir()


@pytest.mark.parametrize("platform", ["win32", "darwin", "linux"])
def test_get_data_dir_raises_when_home_is_file(monkeypatch, tmp_path, platform):
    fake_home = tmp_path / "homefile"
    fake_home.write_text("not a directory")

    monkeypatch.setattr(sys, "platform", platform, raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    with pytest.raises(NotADirectoryError):
        config.get_data_dir()
