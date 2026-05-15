import base64
import re
from pathlib import Path

from app.config import IMG_DIR

_UNSAFE_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\r\n\t]+')


def build_product_image_path(product_name: str) -> str:
    filename = _UNSAFE_FILENAME_CHARS.sub("_", product_name.strip()).strip(" ._")
    if not filename:
        filename = "product"
    return f"img/{filename}.jpg"


def store_product_image(image: str, product_name: str) -> str:
    if not image:
        return ""
    if image.startswith("/img/"):
        return image.lstrip("/")
    if image.startswith("img/") or image.startswith("http"):
        return image
    if not image.startswith("data:"):
        return image

    _, encoded = image.split(",", 1)
    relative_path = build_product_image_path(product_name)
    target_path = IMG_DIR / Path(relative_path).name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(base64.b64decode(encoded))
    return relative_path
