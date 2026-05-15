import os
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_data_dir

APP_NAME = "sis-book"
BACKEND_ROOT = Path(__file__).parents[1]  # 后端根目录

load_dotenv(BACKEND_ROOT / ".env")


def get_data_dir(app_name: str = APP_NAME) -> Path:
    """获取数据目录路径，优先使用环境变量指定的路径，否则使用系统默认路径。"""
    if env_path := os.getenv("SIS_BOOK_DATA"):
        data_path = Path(env_path).expanduser()
    else:
        data_path = Path(user_data_dir(app_name))
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


DATA_DIR = get_data_dir(APP_NAME)            # 数据目录
IMG_DIR = DATA_DIR / "img"                   # 图片目录
DATABASE_PATH = DATA_DIR / "data.db"         # 数据库文件路径
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"  # 数据库连接 URL
