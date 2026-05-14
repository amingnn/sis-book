from pathlib import Path

from app.sync.json_store import read_json, write_json


def get_state(state_path: Path) -> dict:
    return read_json(
        state_path,
        {
            "last_local_signature": "",
            "last_remote_signature": "",
        },
    )


def write_state(state_path: Path, payload: dict) -> None:
    write_json(state_path, payload)
