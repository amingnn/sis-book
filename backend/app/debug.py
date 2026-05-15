import json
import time

from app.config import DATA_DIR

LOG_FILE = DATA_DIR / "debug.log"


def log(message: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps({"ts": time.time(), "msg": message}, ensure_ascii=False) + "\n")
