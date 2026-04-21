import base64
import mimetypes
import re
from pathlib import Path
from shutil import copy2

from app.config import get_data_dir


def _safe_segment(value: str, fallback: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", value).strip()
    cleaned = re.sub(r"\s+", "-", cleaned)
    return cleaned[:80] or fallback


def _relative_image_path(order_number: str, product_name: str, item_index: int, suffix: str) -> str:
    safe_order = _safe_segment(order_number, "order")
    safe_product = _safe_segment(product_name, f"item-{item_index + 1}")
    filename = f"{safe_product}{suffix}"
    return Path("img") / safe_order / safe_product / filename


def store_order_item_image(image: str, order_number: str, product_name: str, item_index: int) -> str:
    if not image:
        return ""

    data_dir = get_data_dir()

    if image.startswith("data:"):
        header, encoded = image.split(",", 1)
        mime_type = header.split(";")[0][5:]
        suffix = mimetypes.guess_extension(mime_type) or ".png"
        relative_path = _relative_image_path(order_number, product_name, item_index, suffix)
        absolute_path = data_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(base64.b64decode(encoded))
        return relative_path.as_posix()

    if image.startswith("img/"):
        source_path = data_dir / image
        if not source_path.exists():
            return image
        relative_path = _relative_image_path(
            order_number,
            product_name,
            item_index,
            source_path.suffix or ".png",
        )
        absolute_path = data_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        if source_path.resolve() != absolute_path.resolve():
            copy2(source_path, absolute_path)
        return relative_path.as_posix()

    return image
