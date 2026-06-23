from pathlib import Path

from app import paths


def test_development_paths_use_project_and_backend_roots():
    project_root = paths.get_project_root()

    assert project_root.name == "sis-book"
    assert paths.get_resource_root() == project_root
    assert paths.get_backend_root() == project_root / "backend"


def test_pyinstaller_paths_use_meipass(monkeypatch, tmp_path):
    meipass = tmp_path / "pyinstaller-root"
    meipass.mkdir()
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "_MEIPASS", str(meipass), raising=False)
    monkeypatch.delattr(paths, "__compiled__", raising=False)

    assert paths.get_resource_root() == meipass
    assert paths.get_backend_root() == meipass


def test_nuitka_paths_prefer_compiled_containing_dir(monkeypatch, tmp_path):
    nuitka_root = tmp_path / "nuitka-dist"
    pyinstaller_root = tmp_path / "pyinstaller-root"
    nuitka_root.mkdir()
    pyinstaller_root.mkdir()

    class Compiled:
        containing_dir = str(nuitka_root)

    monkeypatch.setattr(paths, "__compiled__", Compiled(), raising=False)
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "_MEIPASS", str(pyinstaller_root), raising=False)

    assert paths.get_resource_root() == nuitka_root
    assert paths.get_backend_root() == nuitka_root
