import os
import subprocess
import sys
from pathlib import Path

from app.sync.errors import SyncError


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
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["osascript", "-e", 'POSIX path of (choose folder with prompt "选择目录")'],
                capture_output=True,
                check=False,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return result.stdout.strip().rstrip("/")
            return ""
        except Exception:
            pass

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
