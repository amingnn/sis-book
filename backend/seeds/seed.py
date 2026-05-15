"""生成测试数据。"""
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.customer.models import Customer
from app.database import get_session, init_db
from app.orders.models import SalesOrder, SalesOrderItem
from app.product.models import Product
from app.purchases.models import PurchaseOrder
from app.sales.models import SalesRecord
from app.supplier.models import Supplier
from app.tasks.models import Task
from seeds.sample_data import (
    COLORS,
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


def seed() -> None:
    init_db()
    session = next(get_session())
    product_refs = build_product_refs()

    for name in CUSTOMERS:
        session.add(
            Customer(
                name=name,
                phone=f"1{random.randint(3000000000, 9999999999)}",
                address=random.choice(["浙江省金华市义乌市", "广东省广州市白云区", "江苏省南京市", ""]),
                notes=random.choice(["", "", "重点客户", "月结客户"]),
            )
        )

    for name in SUPPLIERS:
        session.add(
            Supplier(
                name=name,
                phone=f"1{random.randint(3000000000, 9999999999)}",
                address=random.choice(["义乌", "金华", "永康", "浦江", "东阳"]),
                notes=random.choice(["", "", "常用厂家", "价格稳定"]),
            )
        )

    for name, ref in product_refs.items():
        session.add(
            Product(
                name=name,
                image=ref["image"],
                per_box_qty=ref["per_box_qty"],
                box_spec=ref["box_spec"],
                volume=ref["volume"],
                purchase_price=ref["purchase_price"],
                stock_qty=ref["stock_qty"],
                notes=random.choice(["", "", "常规库存", "热销"]),
            )
        )

    for _ in range(20):
        product_name = random.choice(PRODUCTS)
        ref = product_refs[product_name]
        qty = random.randint(100, 3000)
        cost = (ref["purchase_price"] * qty).quantize(Decimal("0.01"))
        margin = Decimal(str(round(random.uniform(0.03, 0.12), 3)))
        amount = (cost * (1 + margin)).quantize(Decimal("0.01"))
        sale_time = rand_date()
        session.add(
            SalesRecord(
                sale_time=sale_time,
                customer_name=random.choice(CUSTOMERS),
                product=product_name,
                amount=amount,
                delivery_time=sale_time + timedelta(days=random.randint(3, 30)) if random.random() > 0.3 else None,
                collection_time=sale_time + timedelta(days=random.randint(20, 60)) if random.random() > 0.5 else None,
                is_settled=random.random() > 0.4,
                payment_method=random.choice(PAYMENT_METHODS),
                cost=cost,
                notes=random.choice(["", "", "", "加急", "含运费", "二次补货", "样品单"]),
            )
        )

    for _ in range(20):
        product_name = random.choice(PRODUCTS)
        ref = product_refs[product_name]
        box_count = random.randint(1, 80)
        per_box_qty = ref["per_box_qty"]
        unit_price = ref["purchase_price"]
        session.add(
            PurchaseOrder(
                purchase_time=rand_date(),
                supplier_name=ref["supplier_name"],
                product_name=product_name,
                box_count=box_count,
                per_box_qty=per_box_qty,
                unit_price=unit_price,
                paid_amount=Decimal(str(round(random.uniform(0, float(unit_price * box_count * per_box_qty)), 2))),
                notes=random.choice(["", "", "", "中包贴标签", "常规包装", "客户提供标签"]),
            )
        )

    for index in range(10):
        sales_date = rand_date()
        order = SalesOrder(
            order_number=f"MC{sales_date.strftime('%Y%m%d')}{index + 1:03d}",
            customer_name=random.choice(CUSTOMERS),
            customer_phone=f"1{random.randint(3000000000, 9999999999)}",
            delivery_address=random.choice(["浙江省金华市义乌市等通知", "广东省广州市白云区XX路", "江苏省南京市XX区", ""]),
            sales_date=sales_date,
            delivery_date=sales_date + timedelta(days=random.randint(5, 20)) if random.random() > 0.3 else None,
            payment_terms=random.choice(["现金", "10%定金 发货付尾款", "月结", "微信"]),
            notes="",
        )
        for _ in range(random.randint(1, 4)):
            product_name = random.choice(PRODUCTS)
            ref = product_refs[product_name]
            order.items.append(
                SalesOrderItem(
                    product_name=product_name,
                    color_spec=random.choice(COLORS),
                    total_boxes=random.randint(1, 50),
                    per_box_qty=ref["per_box_qty"],
                    unit_price=(ref["purchase_price"] * Decimal(str(round(random.uniform(1.03, 1.16), 2)))).quantize(Decimal("0.01")),
                    box_size=ref["box_spec"],
                    image=ref["image"],
                    notes="",
                )
            )
        session.add(order)

    for index in range(15):
        status = random.choice(TASK_STATUSES)
        due_date = datetime.now().date() + timedelta(days=random.randint(-10, 45))
        session.add(
            Task(
                title=f"{random.choice(TASK_CATEGORIES)}任务 {index + 1}",
                description=random.choice(["", "跟进客户确认", "需要复核数量", "等待对方回复"]),
                category=random.choice(TASK_CATEGORIES),
                priority=random.choice(TASK_PRIORITIES),
                status=status,
                due_date=due_date,
                related_type="",
                related_id=None,
                notes=random.choice(["", "", " seed 生成"]),
                completed_at=datetime.now() if status == "done" else None,
            )
        )

    session.commit()
    print("测试数据生成完毕: 客户/厂家/产品资料 + 销售/采购/开单 + 任务")


if __name__ == "__main__":
    seed()
