import sys
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _get_nuitka_containing_dir() -> Path | None:
    compiled = globals().get("__compiled__")
    containing_dir = getattr(compiled, "containing_dir", None)
    if containing_dir:
        return Path(containing_dir)
    return None


def get_resource_root() -> Path:
    nuitka_dir = _get_nuitka_containing_dir()
    if nuitka_dir is not None:
        return nuitka_dir
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return get_project_root()


def is_packaged_runtime() -> bool:
    return _get_nuitka_containing_dir() is not None or getattr(sys, "frozen", False)


def get_backend_root() -> Path:
    resource_root = get_resource_root()
    development_backend = resource_root / "backend"
    if development_backend.exists():
        return development_backend
    return resource_root
