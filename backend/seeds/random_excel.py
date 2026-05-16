"""生成一份可用于导入预览的随机 Excel。"""
import argparse
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.logging import logger
from seeds.sample_data import (
    CUSTOMERS,
    PAYMENT_METHODS,
    PRODUCTS,
    SUPPLIERS,
    TASK_CATEGORIES,
    TASK_PRIORITIES,
    TASK_STATUSES,
    build_product_refs,
    rand_date,
)


def money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def build_workbook_rows() -> dict[str, list[dict]]:
    product_refs = build_product_refs()
    customers = [
        {
            "客户名称": name,
            "电话": f"1{random.randint(3000000000, 9999999999)}",
            "地址": random.choice(["浙江省金华市义乌市", "广东省广州市白云区", "江苏省南京市", ""]),
            "备注": random.choice(["", "重点客户", "月结客户"]),
        }
        for name in CUSTOMERS
    ]
    suppliers = [
        {
            "厂家名称": name,
            "电话": f"1{random.randint(3000000000, 9999999999)}",
            "地址": random.choice(["义乌", "金华", "永康", "浦江", "东阳"]),
            "备注": random.choice(["", "常用厂家", "价格稳定"]),
        }
        for name in SUPPLIERS
    ]
    products = [
        {
            "产品名称": name,
            "图片": ref["image"],
            "装箱数": ref["per_box_qty"],
            "箱规": ref["box_spec"],
            "体积": float(ref["volume"]),
            "进货价格": money(ref["purchase_price"]),
            "库存数量": ref["stock_qty"],
            "备注": random.choice(["", "常规库存", "热销"]),
        }
        for name, ref in product_refs.items()
    ]

    sales = []
    for _ in range(20):
        product_name = random.choice(PRODUCTS)
        ref = product_refs[product_name]
        qty = random.randint(100, 3000)
        cost = (ref["purchase_price"] * qty).quantize(Decimal("0.01"))
        amount = (cost * Decimal(str(round(random.uniform(1.03, 1.16), 2)))).quantize(Decimal("0.01"))
        sale_time = rand_date()
        sales.append(
            {
                "销售时间": sale_time.isoformat(),
                "客户名称": random.choice(CUSTOMERS),
                "产品": product_name,
                "销售金额": money(amount),
                "送货时间": (sale_time + timedelta(days=random.randint(3, 30))).isoformat(),
                "收款时间": (sale_time + timedelta(days=random.randint(20, 60))).isoformat(),
                "是否结清": random.choice(["是", "否"]),
                "交易方式": random.choice(PAYMENT_METHODS),
                "成本": money(cost),
                "备注": random.choice(["", "加急", "含运费", "样品单"]),
            }
        )

    purchases = []
    for _ in range(20):
        product_name = random.choice(PRODUCTS)
        ref = product_refs[product_name]
        box_count = random.randint(1, 80)
        total = ref["purchase_price"] * box_count * ref["per_box_qty"]
        purchases.append(
            {
                "采购时间": rand_date().isoformat(),
                "厂家名称": ref["supplier_name"],
                "产品名称": product_name,
                "箱数": box_count,
                "装箱数": ref["per_box_qty"],
                "单价": money(ref["purchase_price"]),
                "已付金额": money(Decimal(str(round(random.uniform(0, float(total)), 2)))),
                "备注": random.choice(["", "中包贴标签", "常规包装", "客户提供标签"]),
            }
        )

    tasks = [
        {
            "标题": f"{random.choice(TASK_CATEGORIES)}任务 {index + 1}",
            "描述": random.choice(["", "跟进客户确认", "需要复核数量", "等待对方回复"]),
            "分类": random.choice(TASK_CATEGORIES),
            "优先级": random.choice(TASK_PRIORITIES),
            "状态": random.choice(TASK_STATUSES),
            "到期日期": (datetime.now().date() + timedelta(days=random.randint(-10, 45))).isoformat(),
            "关联类型": "",
            "关联ID": "",
            "备注": random.choice(["", "Excel 随机生成"]),
        }
        for index in range(15)
    ]

    return {
        "客户": customers,
        "厂家": suppliers,
        "产品": products,
        "销售": sales,
        "采购": purchases,
        "任务": tasks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="生成随机导入 Excel")
    parser.add_argument(
        "output",
        nargs="?",
        default=str(Path(__file__).with_name("random-import.xlsx")),
        help="输出 Excel 路径，默认写到 seeds/random-import.xlsx",
    )
    args = parser.parse_args()

    output_path = Path(args.output).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, rows in build_workbook_rows().items():
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, index=False)
    logger.success("随机 Excel 已生成：{}", output_path)


if __name__ == "__main__":
    main()
