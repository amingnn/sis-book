import shutil
from pathlib import Path


def list_files(root: Path) -> list[dict]:
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


def mirror_directory(source_dir: Path, target_dir: Path) -> None:
    source_files = {file["path"]: file for file in list_files(source_dir)}
    target_files = {file["path"]: file for file in list_files(target_dir)}

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
