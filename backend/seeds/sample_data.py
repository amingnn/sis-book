import random
from datetime import date, timedelta
from decimal import Decimal

from app.product.images import build_product_image_path

CUSTOMERS = ["福瑞鑫", "JT", "通远", "鑫达贸易", "华盛商行", "金利来", "宏达玩具", "乐天商贸", "万家福", "顺发百货"]
PRODUCTS = ["鹿牌球", "PVC球", "跳跳马", "弹力球", "充气玩具", "网棒混装", "贴标球", "新蛇混款", "足球", "篮球"]
SUPPLIERS = ["博扬球业", "昇利隆玩具", "金华塑胶", "永康运动", "浦江文体", "东阳玩具厂", "武义球业"]
COLORS = ["5款混色", "5色混标", "红蓝混", "彩色混装", "单色", "3色混", "随机混色"]
PAYMENT_METHODS = ["现金", "45天", "30天", "微信", "银行转账", "月结"]
BOX_QTYS = [50, 100, 200, 300, 500, 600]
TASK_CATEGORIES = ["收款", "发货", "采购", "对账", "售后", "其他"]
TASK_PRIORITIES = ["low", "medium", "high"]
TASK_STATUSES = ["todo", "doing", "done"]


def rand_date(start_year: int = 2025) -> date:
    start = date(start_year, 1, 1)
    return start + timedelta(days=random.randint(0, 460))


def build_product_refs() -> dict[str, dict]:
    refs = {}
    for product in PRODUCTS:
        refs[product] = {
            "supplier_name": random.choice(SUPPLIERS),
            "image": build_product_image_path(product),
            "per_box_qty": random.choice(BOX_QTYS),
            "box_spec": f"{random.randint(45, 80)}*{random.randint(30, 55)}*{random.randint(25, 50)}",
            "volume": Decimal(str(round(random.uniform(0.03, 0.18), 3))),
            "purchase_price": Decimal(str(round(random.uniform(0.3, 8.0), 2))),
            "stock_qty": random.randint(0, 5000),
        }
    return refs
