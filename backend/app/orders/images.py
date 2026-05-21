import base64
import re
from pathlib import Path

from app.config import IMG_DIR

_UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]+')


def _safe_path_part(value: str, fallback: str) -> str:
    safe = _UNSAFE_FILENAME_CHARS.sub("_", value.strip()).strip(" ._")
    return safe or fallback


def build_order_item_image_path(order_number: str, product_name: str) -> str:
    order_dir = _safe_path_part(order_number, "order")
    filename = f"{_safe_path_part(product_name, 'product')}.jpg"
    return f"img/{order_dir}/{filename}"


def store_order_item_image(image: str, order_number: str, product_name: str) -> str:
    if not image:
        return ""
    if image.startswith("/img/"):
        return image.lstrip("/")
    if image.startswith("img/") or image.startswith("http"):
        return image
    if not image.startswith("data:"):
        return image

    _, encoded = image.split(",", 1)
    relative_path = build_order_item_image_path(order_number, product_name)
    target_path = IMG_DIR / Path(relative_path.removeprefix("img/"))
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(base64.b64decode(encoded))
    return relative_path
