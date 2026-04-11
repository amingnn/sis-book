"""生成测试数据"""
import random
from datetime import date, timedelta
from decimal import Decimal

from app.database import init_db, get_session
from app.sales.models import SalesRecord
from app.purchases.models import PurchaseOrder
from app.orders.models import SalesOrder, SalesOrderItem

CUSTOMERS = ["福瑞鑫", "JT", "通远", "鑫达贸易", "华盛商行", "金利来", "宏达玩具", "乐天商贸", "万家福", "顺发百货"]
PRODUCTS = ["鹿牌球", "PVC球", "跳跳马", "弹力球", "充气玩具", "网棒混装", "贴标球", "新蛇混款", "足球", "篮球"]
SUPPLIERS = ["博扬球业", "昇利隆玩具", "金华塑胶", "永康运动", "浦江文体", "东阳玩具厂", "武义球业"]
COLORS = ["5款混色", "5色混标", "红蓝混", "彩色混装", "单色", "3色混", "随机混色"]
PAYMENT_METHODS = ["现金", "45天", "30天", "微信", "银行转账", "月结"]

def rand_date(start_year=2025) -> date:
    start = date(start_year, 1, 1)
    return start + timedelta(days=random.randint(0, 460))

def seed():
    init_db()
    session = next(get_session())

    # 销售记录 20 条
    for _ in range(20):
        cost = Decimal(random.randint(500, 150000))
        margin = Decimal(str(round(random.uniform(0.03, 0.12), 3)))
        amount = (cost * (1 + margin)).quantize(Decimal("0.01"))
        sale_time = rand_date()
        record = SalesRecord(
            sale_time=sale_time,
            customer_name=random.choice(CUSTOMERS),
            product=random.choice(PRODUCTS),
            amount=amount,
            delivery_time=sale_time + timedelta(days=random.randint(3, 30)) if random.random() > 0.3 else None,
            is_settled=random.random() > 0.4,
            payment_method=random.choice(PAYMENT_METHODS),
            cost=cost,
            notes=random.choice(["", "", "", "加急", "含运费", "二次补货", "样品单"]),
        )
        session.add(record)

    # 采购记录 20 条
    for _ in range(20):
        box_count = random.randint(1, 80)
        per_box_qty = random.choice([50, 100, 200, 300, 500, 600])
        unit_price = Decimal(str(round(random.uniform(0.3, 8.0), 2)))
        po = PurchaseOrder(
            purchase_time=rand_date(),
            supplier_name=random.choice(SUPPLIERS),
            product_name=random.choice(PRODUCTS),
            box_count=box_count,
            per_box_qty=per_box_qty,
            unit_price=unit_price,
            notes=random.choice(["", "", "", "中包贴标签", "常规包装", "客户提供标签"]),
        )
        session.add(po)

    # 销售单 10 条
    for i in range(10):
        sales_date = rand_date()
        order = SalesOrder(
            order_number=f"MC{sales_date.strftime('%Y%m%d')}{i+1:03d}",
            customer_name=random.choice(CUSTOMERS),
            customer_phone=f"1{random.randint(3000000000, 9999999999)}",
            delivery_address=random.choice(["浙江省金华市义乌市等通知", "广东省广州市白云区XX路", "江苏省南京市XX区", ""]),
            sales_date=sales_date,
            delivery_date=sales_date + timedelta(days=random.randint(5, 20)) if random.random() > 0.3 else None,
            payment_terms=random.choice(["现金", "10%定金 发货付尾款", "月结", "微信"]),
            notes="",
        )
        item_count = random.randint(1, 4)
        for _ in range(item_count):
            item = SalesOrderItem(
                product_name=random.choice(PRODUCTS),
                color_spec=random.choice(COLORS),
                total_boxes=random.randint(1, 50),
                per_box_qty=random.choice([50, 100, 200, 300, 600]),
                unit_price=Decimal(str(round(random.uniform(0.5, 6.0), 2))),
                box_size=f"{round(random.uniform(0.01, 0.2), 3)}",
                notes="",
            ) # type: ignore
            order.items.append(item)
        session.add(order)

    session.commit()
    print("测试数据生成完毕: 20条销售记录 + 20条采购记录 + 10张销售单")

if __name__ == "__main__":
    seed()
